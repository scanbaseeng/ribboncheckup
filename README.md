# ribboncheckup.org

Static site. No dependencies beyond Python 3.

- `src/content/<section>/*.md` articles; sections are `articles`, `guides`, `health-explained`, `preventive-health`
- `src/pages/*.md` about, privacy, disclaimer
- `src/style.css` styles
- `build.py` generates `site/`

Build locally: `python3 build.py` then open `site/index.html`.

## Deploy

1. Push to a GitHub repo, branch `main`.
2. Repo Settings > Pages > Source: **GitHub Actions**.
3. Settings > Pages > Custom domain: `ribboncheckup.org`. Check "Enforce HTTPS" once the certificate issues.

## Porkbun DNS

Porkbun > Domain Management > ribboncheckup.org > DNS Records. Delete the default parking ALIAS and CNAME records Porkbun adds, then create:

| Type  | Host | Answer                          | TTL |
|-------|------|---------------------------------|-----|
| A     | (blank) | 185.199.108.153              | 600 |
| A     | (blank) | 185.199.109.153              | 600 |
| A     | (blank) | 185.199.110.153              | 600 |
| A     | (blank) | 185.199.111.153              | 600 |
| CNAME | www  | `scanbaseeng.github.io`   | 600 |

Leave the Host field empty for the root records. Porkbun offers ALIAS records for the root; use plain A records instead, since GitHub verifies against the A record IPs.

Then in the repo: Settings > Pages > Custom domain: `ribboncheckup.org` > Save. GitHub runs a DNS check. Once it passes, tick "Enforce HTTPS". Certificate issuance can take up to an hour.

Optional: Settings > Pages in your GitHub *account* > "Add a domain" to verify ribboncheckup.org. That prevents anyone else's Pages site from claiming the domain if you ever remove it.

## Add an article

Copy any file in the matching `src/content/<section>/` folder, change the frontmatter (`title`, `description`, `category`, `date`, `order`), write the body, push.
