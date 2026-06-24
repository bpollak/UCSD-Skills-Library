---
name: email-communication-policy
description: |
  Governs ALL outbound email on behalf of the user. NEVER send without explicit
  approval. Always draft first and save to Drafts folder. Always reply to the
  original thread for replies. Required reading before any email operation.
catalog:
  title: Email Communication Policy
  description: >-
    Governs all outbound email on behalf of the user. Draft-only workflow with
    verified signature, TritonAI Harness disclosure, and thread-safe replies.
  category: Campus AI Tools
  status: built
  publicationStatus: draft
  tier: experimental
  owner: AI Tools
  updated: 2026-06-23
allowed-tools: Read, Bash
---

# Email Communication Policy

## Core Rules

1. **Never send email without explicit approval.** Draft first, save to Drafts, then ask the user to review and hit send or say "approve".

2. **For replies: always reply to the original thread.** Use `createReply` on the source message to preserve threading (In-Reply-To, References, ConversationId headers). Never compose a new message when responding to an existing thread.

3. **For new emails:** Create a draft in the Drafts folder.

4. **Load user's email style preferences from** `~/.config/email-preferences/config.json` **before drafting.** The config contains the user's font, salutation format, sign-off, signature block, full name, and title. All email drafts must use these values — do not hardcode any personal details in the skill or workflow.

5. **Signature** must be appended to every email body (after the message content, before any disclosure line). Use the user's verified signature from the config file (`signature` block).

6. **Disclosure line:** After the signature, add a separator and disclosure:

   ```
   ---
   Drafted with assistance from the TritonAI Harness
   ```

   The disclosure makes it clear the draft is AI-assisted. The user can remove or keep this line before hitting send.

## Technical Implementation

### Prerequisites

- The `ucsd-msgraph-calendar` skill must have a valid token with `Mail.Read`, `Mail.ReadWrite`, and `Mail.Send` scopes cached. `Mail.ReadWrite` is required for creating drafts in the Drafts folder.
- Config scopes in `~/.config/ucsd-msgraph-calendar/config.json` must include `Mail.ReadWrite`.
- If token is expired, run the `--force` re-auth flow first.

### API Endpoints (Microsoft Graph v1.0)

| Action | Endpoint | Method |
|--------|----------|--------|
| Get message by ID | `/me/messages/{messageId}` | GET |
| Get thread messages | `/me/messages?$filter=conversationId eq '{conversationId}'` | GET |
| Create reply draft | `/me/messages/{messageId}/createReply` | POST |
| Update draft body | `/me/messages/{draftId}` | PATCH |
| **Create new draft in Drafts folder** | **`/me/mailFolders/Drafts/messages`** | **POST** |
| Send approved draft | `/me/messages/{draftId}/send` | POST |
| Delete draft | `/me/messages/{draftId}` | DELETE |

### Workflow: Drafting a new email

```
1. Load email preferences from ~/.config/email-preferences/config.json
2. From the config, extract:
   - signature.font_family, signature.font_size, signature.font_color
   - style.salutation_format (e.g. "Hi {name},")
   - signature.email_sign_off (e.g. "Thanks, {name}")
   - signature.full_name, signature.title, signature.organization
   - style.body_content_type (must be "HTML")
3. Compose message body as HTML using the user's style:
   <html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head>
   <body>
   <div style="direction:ltr; font-family:{font_family}; font-size:{font_size}; color:{font_color}">
   {salutation_line}
   <br><br>
   {body content with <br> line breaks}
   <br><br>
   {sign_off_line}<br>
   {full_name}
   </div></body></html>
4. POST /me/mailFolders/Drafts/messages
   {
     "subject": "...",
     "body": {"contentType": "HTML", "content": "..."},
     "toRecipients": [{"emailAddress": {"address": "..."}}],
     "ccRecipients": [...]
   }
5. Confirm draft created — return the draft ID to the user
6. Tell the user: "Draft saved to your Drafts folder. Review and hit send when ready, or say 'approve' and I'll send it."
```

### Workflow: Replying to a thread

```
1. Identify the source message (from context or user)
2. GET /me/messages/{messageId} to get conversationId, subject
3. POST /me/messages/{messageId}/createReply
   — This creates a draft in Drafts with proper In-Reply-To and References headers
4. PATCH /me/messages/{draftId}
   — Update the body with reply content + signature + disclosure
5. Confirm draft created to user
```

### Workflow: Approval & Send

When user says "approve" (or similar):
```
1. GET the draft message to verify content
2. Remove the disclosure line from the body
3. PATCH /me/messages/{draftId} with cleaned body
4. POST /me/messages/{draftId}/send
5. Confirm sent to user
```

OR the user can manually open the draft in Outlook and hit send themselves.

## Guardrails

- **Never send without explicit approval.** "Do you want me to send this?" is always required.
- **Drafts only.** Always save to Drafts folder (`/me/mailFolders/Drafts/messages`).
- **Thread integrity.** For replies, always use `createReply` — never compose a new message for a thread response.
- **Disclosure required.** Every draft must include the TritonAI Harness disclosure line until approved.
- **Signature consistent.** Use the exact signature format shown above (name, title, org).
- **Style consistent.** Always load `~/.config/email-preferences/config.json` and use the user's font, salutation, and sign-off format.
- **No impersonation.** The disclosure line distinguishes AI-assisted drafts from direct human communication.
- **Body content only.** Never read email bodies unless the user explicitly requests it for drafting context.
- **Review before send.** After user approves, show a final summary: To, Subject, and first/last 100 chars of body.

## Dependencies

- Microsoft Graph API v1.0
- Valid OAuth token with `Mail.Read`, `Mail.ReadWrite`, and `Mail.Send` scopes (from ucsd-msgraph-calendar skill)
- `msal` and `requests` Python libraries
- `~/.config/email-preferences/config.json` — user's personal email style (auto-created with defaults on first use)

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | This policy file |
| `~/.config/email-preferences/config.json` | User's email style preferences (font, salutation, sign-off) |
| `~/.config/ucsd-msgraph-calendar/config.json` | Microsoft Graph auth config (must include `Mail.ReadWrite` scope) |
