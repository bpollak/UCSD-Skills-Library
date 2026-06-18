# Azure AD App Registration for Microsoft Graph Calendar

Current as of: June 2026

## Step-by-step

1. **Go to Microsoft Entra admin center**
   - Open https://entra.microsoft.com
   - Navigate to **Applications** → **App registrations**

2. **Create a new app registration**
   - Click **+ New registration**
   - **Name:** `TritonAI Calendar` (or any descriptive name)
   - **Supported account types:** *Accounts in this organizational directory only* (single tenant)
   - **Redirect URI:** Leave blank — device code flow does not need a redirect URI
   - Click **Register**

3. **Copy the IDs**
   After registration, you'll see the app's overview page. Copy these two values:
   - **Application (client) ID** → goes in `config.json` as `client_id`
   - **Directory (tenant) ID** → goes in `config.json` as `tenant_id`

4. **Enable public client flows**
   - In the left menu, click **Authentication**
   - Under **Advanced settings**, set **Allow public client flows** to **Yes**
   - Click **Save**

5. **Add API permissions**
   - In the left menu, click **API permissions**
   - Click **+ Add a permission**
   - Choose **Microsoft Graph** → **Delegated permissions**
   - Search for and select:
     - `Calendars.Read` — read events in your calendars
     - `User.Read` — sign-in and read your profile
   - Click **Add permissions**

6. **Grant admin consent** (if applicable)
   - If you have admin privileges, click **Grant admin consent** and confirm
   - If not, ask your Microsoft 365 administrator to grant consent for the organization
   - Without admin consent, each user will need to consent on first sign-in (which works with device code flow)

7. **Configure the skill**
   - Edit `~/.config/ucsd-msgraph-calendar/config.json`
   - Fill in `client_id` and `tenant_id` from step 3
   - Set `account_hint` to your email (e.g., `bpollak@ucsd.edu`)

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `AADSTS700016: Application with identifier was not found` | Wrong `client_id` or `tenant_id` | Double-check values from app registration |
| `AADSTS650052: The app needs access to a service` | API permissions not granted | Check Calendars.Read and User.Read are added and consented |
| `AADSTS7000222: The provided client secret keys are empty` | App not configured as public client | Set "Allow public client flows" to Yes |
| Token refresh fails after ~90 days | Refresh token expired | Run with `--force` to re-authenticate |

## Azure portal links

- App registrations: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
- Your organization's apps: https://portal.azure.com/#blade/Microsoft_AAD_IAM/StartboardApplicationsMenuBlade/AllApps
