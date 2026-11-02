# Putting the website on privacy.peterparker.ca

The website is `site/`. It has two pages, a stylesheet, one script, two fonts, the four
architecture diagrams and `data.json`. There is no backend, so hosting it is a file upload and
one DNS record. It follows the same path as the other project pages on peterparker.ca, and is
styled like them.

**Every number on the page comes from `site/data.json`**, and none is typed by hand.
`facsimile site` writes the file from the same committed results as the README's tables
(`facsimile report`). It adds the distance-to-closest-record yardstick from
`results/<dataset>/dcr_null.json`. In CI, `tests/test_site.py` fails if the committed file has
fallen behind the results. It also fails if the script looks for an element the page no longer
has.

When the results change, run `facsimile report`, then `facsimile site`, and commit
`site/data.json` with the tables.

Steps 1 to 3 are done once, by Peter, in the Azure portal, the Cloudflare dashboard and GitHub.
Step 4 is automatic after that.

**Deployed 2026-11-01.** The app is `privacy-peterparker-ca` in resource group `rg-portfolio-2`
(East US 2, Free), served at `delightful-grass-0b492c10f.5.azurestaticapps.net`. It is in its own
subscription, `PAP-POCs 2`, created for it the same day under the same billing account: the
subscription holding the other project pages (`rg-portfolio`) had reached Azure's limit of ten
Free static web apps, and every one of the ten serves a live site. The Free plan costs nothing in
either subscription. The deploy token is the repository secret, `SITE` is `on`, and the first
upload ran from `.github/workflows/site.yml`. The custom domain waits on the CNAME at Cloudflare
(step 2).

## 0. Check the subscription before creating anything

```powershell
az login
az account set --subscription <subscription>
az staticwebapp list -o table              # the subscription's existing apps
```

## 1. Create the Static Web App

Portal: Create a resource, **Static Web App**.

| Setting | Value |
|---|---|
| Subscription | `<subscription>` |
| Resource group | `<resource-group>` |
| Name | `privacy-peterparker-ca` |
| Plan type | **Free** |
| Region | any; content is served from a CDN regardless |
| Deployment source | **Other** |

**Choose "Other", not GitHub.** The GitHub option commits a workflow of its own and wires a
credential into the repository. This repository already has its workflow
(`.github/workflows/site.yml`), and the credential goes in GitHub's secret store in step 3.

Or from the CLI:

```powershell
az staticwebapp create --name privacy-peterparker-ca --resource-group <resource-group> `
  --location eastus2 --sku Free --subscription <subscription>
```

## 2. The DNS record, at Cloudflare

1. Copy the app's URL from its **Overview** page: `https://<generated-name>.azurestaticapps.net`.
2. In the Cloudflare dashboard, open `peterparker.ca`, then **DNS**, **Records**, **Add record**:

   | Type | Name | Target | Proxy status | TTL |
   |---|---|---|---|---|
   | CNAME | `privacy` | `<generated-name>.azurestaticapps.net` | **DNS only** | Auto |

3. **Proxy status DNS only, the grey cloud.** A proxied record hides the target behind
   Cloudflare's addresses. Azure's validation then cannot see the CNAME, and the certificate is
   never issued.
4. Add the custom domain to the app:

   ```powershell
   az staticwebapp hostname set --name privacy-peterparker-ca --resource-group <resource-group> `
     --hostname privacy.peterparker.ca --subscription <subscription>
   ```

5. Wait for validation, usually minutes. Azure issues and renews the certificate itself.

## 3. The deploy token and the switch, in GitHub

The token goes into the repository's secret store straight from the Azure CLI, so it never
appears on screen, in a file or in shell history. **The token alone is enough to publish to the
site.**

```powershell
az staticwebapp secrets list --name privacy-peterparker-ca --resource-group <resource-group> `
  --subscription <subscription> --query properties.apiKey -o tsv |
  gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo Peter-A-P/privacy-safe-data-sharing

gh variable set SITE --body on --repo Peter-A-P/privacy-safe-data-sharing
```

Until `SITE` is `on`, every run of the website workflow skips rather than failing.

## 4. Publish

From here it is automatic: every push to `main` that changes `site/` uploads it. To publish now:

```powershell
gh workflow run site.yml --repo Peter-A-P/privacy-safe-data-sharing
```

Then give the project's entry in peterparker.ca's `projects.yaml` a `demo:` address and a
`demo_note:`, so the project page carries the button.

## 5. Check it

- Look at it locally with the host's security headers. `python -m http.server` sends none of
  them, so it shows a page the content security policy might partly refuse. The policy is in
  `site/staticwebapp.config.json`.
- `https://privacy.peterparker.ca` serves over HTTPS with no certificate warning.
- The browser console on the live page is empty. A policy violation is reported there and
  nowhere else.
- The hero's figures match the README:
  - the tables attacked;
  - the one named leak;
  - no configuration recommended;
  - distance to closest record's false alarms.

Cost: the Free plan, CA$0.
