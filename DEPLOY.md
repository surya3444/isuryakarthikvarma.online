# Deploying isuryakarthikvarma.online + your products

You want two things on one domain:
1. **The portfolio site** (this repo) — a static page.
2. **Your products** (Propertyverse, Grape CRM, etc.) — mostly Frappe/Python apps.

The clean way to do both is **one VPS + subdomains**, with the portfolio either on the same box or on a free static host. Here are the two routes.

---

## Route A — Everything on one VPS (recommended, since you know Python & Frappe)

This gives you a real server you fully control, and lets you deploy Frappe products under your own domain.

**Layout:**
```
isuryakarthikvarma.online              → portfolio (this static site)
propertyverse.isuryakarthikvarma.online → Frappe site (Propertyverse)
crm.isuryakarthikvarma.online           → Frappe site (Grape CRM)
api.isuryakarthikvarma.online           → any Python/Node service
```

### 1. Get a VPS
Hetzner, DigitalOcean, or Contabo. A 2 vCPU / 4 GB box (~$5–12/mo) runs a couple of Frappe sites fine. Ubuntu 22.04.

### 2. Point DNS (at your domain registrar)
Create these records:
```
A     @                    <your-server-ip>
A     www                  <your-server-ip>
A     *                    <your-server-ip>   # wildcard → all subdomains hit the server
```
The wildcard `*` means every `<anything>.isuryakarthikvarma.online` lands on your box, so you can add products without touching DNS again.

### 3. Serve the portfolio with nginx
```bash
sudo apt update && sudo apt install nginx -y
sudo mkdir -p /var/www/portfolio
# upload index.html into /var/www/portfolio (scp, git clone, or rsync)
```
`/etc/nginx/sites-available/portfolio`:
```nginx
server {
    server_name isuryakarthikvarma.online www.isuryakarthikvarma.online;
    root /var/www/portfolio;
    index index.html;
    location / { try_files $uri $uri/ =404; }
}
```
```bash
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d isuryakarthikvarma.online -d www.isuryakarthikvarma.online   # free HTTPS
```

### 4. Install Frappe Bench (for your products)
```bash
# Follow the official installer, then:
bench init frappe-bench --frappe-branch version-15
cd frappe-bench

# One site per product, each on its own subdomain:
bench new-site propertyverse.isuryakarthikvarma.online
bench get-app <your-propertyverse-frappe-app>
bench --site propertyverse.isuryakarthikvarma.online install-app propertyverse

# Make it production (nginx + supervisor + HTTPS):
sudo bench setup production <your-linux-user>
bench setup add-domain propertyverse.isuryakarthikvarma.online --site propertyverse.isuryakarthikvarma.online
sudo bench setup lets-encrypt propertyverse.isuryakarthikvarma.online
```
Frappe's `bench` manages nginx configs for its sites; keep your portfolio's nginx file separate and it won't conflict.

> Note: several of your current repos (propertyverse, Grape CRM) are TS/JS, not Frappe apps yet. Those deploy the same way as any Node app — run them with `pm2`, put nginx in front on a subdomain, and add a Let's Encrypt cert. Mix and match: Frappe sites for the ERP-style products, Node/pm2 for the JS ones.

---

## Route B — Split hosting (fastest to go live today)

- **Portfolio** → deploy `index.html` to **Cloudflare Pages / Netlify / Vercel** (free, global CDN, auto-HTTPS). Point the root domain there.
- **Products** → each on its own subdomain pointing at a VPS or a platform like Railway/Render.

**To ship the portfolio in 2 minutes right now:**
```bash
# Option 1: GitHub Pages
#   push this folder to a repo, Settings → Pages → deploy from main, then add
#   isuryakarthikvarma.online as a custom domain.

# Option 2: Netlify drop
#   go to app.netlify.com/drop and drag this folder in, then add your custom domain.
```
Then in DNS, add the CNAME/records the host tells you for the root, and keep an `A *` wildcard pointing at your product VPS.

---

## My recommendation

Start with **Route B for the portfolio** (live today, zero maintenance) and stand up **Route A's VPS** when you're ready to deploy your first product on a subdomain. You get a professional front door immediately and a real product server when you need it — all under the one domain.
