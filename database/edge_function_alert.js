// Supabase Edge Function: send-matched-videos
// - Calls Postgres RPC function get_keyword_matches()
// - Sends an email via Resend with a list of matched videos
// - Does NOT send an email when there are no matches

import { createClient } from "npm:@supabase/supabase-js@2";

const RESEND_ENDPOINT = "https://api.resend.com/emails";

Deno.serve(async (req) => {
  if (req.method !== "POST" && req.method !== "GET") {
    return new Response("Method not allowed", { status: 405 });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL");
  const serviceRoleKey = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (!supabaseUrl || !serviceRoleKey) {
    return new Response("Missing Supabase env vars", { status: 500 });
  }

  const supabaseAdmin = createClient(supabaseUrl, serviceRoleKey);

  const resendApiKey = Deno.env.get("RESEND_API_KEY");
  const fromEmail = Deno.env.get("RESEND_FROM_EMAIL");
  const toEmail = Deno.env.get("RESEND_TO_EMAIL");
  if (!resendApiKey || !fromEmail || !toEmail) {
    return new Response(
      "Missing Resend env vars (RESEND_API_KEY, RESEND_FROM_EMAIL, RESEND_TO_EMAIL)",
      { status: 500 }
    );
  }

  const { data, error } = await supabaseAdmin.rpc("get_keyword_matches");
  if (error) {
    return new Response(`RPC error: ${error.message}`, { status: 500 });
  }

  const matches = Array.isArray(data) ? data : [];

  // ✅ If no matches, do not send email
  if (matches.length === 0) {
    return new Response(
      JSON.stringify({ sent: false, matchesCount: 0, reason: "no_matches" }),
      { headers: { "Content-Type": "application/json" }, status: 200 }
    );
  }

const escapeHtml = (str) =>
  String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const listHtml = `
  <div>
    ${matches
      .map((m) => {
        const sourceName = escapeHtml(m.source_name);
        const title = escapeHtml(m.title);
        const url = escapeHtml(m.url);
        const summary = escapeHtml(m.summary);
        const media = escapeHtml(m.media);

        return `
          <div style="
            display: flex;
            flex-direction: row;
            gap: 12px;
            width: 100%;
            padding: 12px;
            border: 1px solid #e5e5e5;
            border-radius: 10px;
            background: #fff;
            box-sizing: border-box;
          ">

            <!-- Image -->
            <img
              src="${media}"
              alt="${title}"
              style="
                width: 140px;
                height: 90px;
                object-fit: cover;
                border-radius: 8px;
                flex-shrink: 0;
                margin-right:5px
              "
            />

            <!-- Content -->
            <div>
              
              <div style="font-size: 12px; color: #666; margin-bottom:10px">
                ${sourceName}
              </div>

              <a
                href="${url}"
                target="_blank"
                rel="noopener noreferrer"
                style="font-size: 14px; font-weight: 600; color: #1a73e8; text-decoration: none; margin-bottom:10px"
              >
                ${title}
              </a>

              <p style="margin: 0; font-size: 13px; color: #444; line-height: 1.4;">
                ${summary}
              </p>

            </div>
          </div>
        `;
      })
      .join("")}
  </div>
`;

const html = `
  <h2 style="font-family: sans-serif;">Your matched videos</h2>
  ${listHtml}
`;

  const subject = `Your matched videos (${matches.length})`;

  const resendRes = await fetch(RESEND_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${resendApiKey}`,
    },
    body: JSON.stringify({
      from: fromEmail,
      to: [toEmail],
      subject,
      html,
    }),
  });

  if (!resendRes.ok) {
    const text = await resendRes.text().catch(() => "");
    return new Response(
      `Resend error: ${resendRes.status} ${resendRes.statusText} ${text}`.trim(),
      { status: 502 }
    );
  }

  return new Response(
    JSON.stringify({ sent: true, matchesCount: matches.length }),
    { headers: { "Content-Type": "application/json" }, status: 200 }
  );
});
