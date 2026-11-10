# R-a: VPS aur Network Research (Phase 1, sirf docs)

**Tarikh:** 10 Nov 2026. **Status:** sirf research. Production code nahi hai. Upstox se login ya auth request nahi bheji gayi. Sirf DNS/RDAP lookup aur public docs padhe gaye.
**Source tags:** `[S#]` ka matlab neeche "Sources" list ki entry hai. Har source **10 Nov 2026** ko dekha gaya ("dekha: 10 Nov 2026").
**Shabd:** "andaza" = mera anumaan, kisi official page par nahi likha. "verify nahi hua" = internet se confirm nahi ho saka.

---

## Saar (10 line)

1. Upstox ka order host `api-hft.upstox.com` aur market-data WebSocket host `wsfeeder-api.upstox.com` dono **AWS Mumbai (ap-south-1) ke ELB** par hain. Yeh DNS CNAME, AWS ip-ranges aur ARIN RDAP teeno se confirm hua [S1][S2][S3].
2. `api.upstox.com` (login, auth, GTT, kill switch, portfolio WS) **Cloudflare** ke peeche hai. Origin kahan hai, yeh verify nahi hua [S1][S3].
3. Isliye **Bot ke liye AWS ap-south-1 sabse paas ka cloud hai**. Public RTT measurement kahin nahi mila, isliye verify nahi hua. Isse humein khud probe karke naapna hoga.
4. Static IP niyam: har **user** ko 1 Primary + 1 Secondary IP milta hai. IP **hafte mein ek baar** badal sakte hain, aur badalte hi saare access token invalid ho jaate hain. IPv4 aur IPv6 dono notation chalte hain [S5][S6][S7].
5. **Bada khatra:** 1 Apr 2026 se **ek user ka sirf ek active API app** chalega [S10]. Matlab "Pehredaar ka alag Upstox app" wala plan shayad mumkin nahi. Token share karne ka design D2 mein tay karna hoga.
6. Market-data WebSocket mein Standard user ko **2 connection** milte hain [S13]. Bot 1 lega, Pehredaar 1. Dashboard ko WebSocket nahi kholna chahiye.
7. **Bot:** AWS `c8g.xlarge` (4 Graviton4 physical core, 8 GiB), lagbhag **$78.81/mahina** [S16][S18]. Precision-time (PHC) clock support karta hai [S21].
8. **Pehredaar:** GCP Mumbai `c4a-standard-2` (Axion, 1 vCPU = 1 poora core), lagbhag $68.17/mahina [S28][S31]. Plan B: Azure Central India `D2ps_v6`, jo $33.73 hai par **Pune mein** hai [S36][S40]. Ya Akamai Mumbai Dedicated 4GB ($36) [S52].
9. 3 machine ka kharcha (sirf andaza, GST alag): **(i) sab AWS, alag AZ: ~$147/mahina (~₹13,830)**. **(ii) Pehredaar GCP par: ~$176 (~₹16,521)**. INR rate ECB cross rate se liya [S60]. AWS India 18% GST lagata hai [S61].
10. Kuch bhi khareedne se pehle: 3 trial VM par 5 trading din probe chalao (Section 6), aur Upstox se 3 sawaal confirm karo (Section 8, "verify nahi hua" list).

---

## 1. Upstox hosting findings

### 1.1 Tarika
- `python socket.getaddrinfo` aur Google DNS-over-HTTPS (`dns.google/resolve`) se A, AAAA aur CNAME records nikale [S1].
- IP ka owner ARIN RDAP (`rdap.arin.net`) se dekha [S3].
- AWS IPs ko AWS ki official `ip-ranges.json` (createDate 2026-11-09) se match kiya [S2].
- Upstox ko koi HTTP ya auth request **nahi** bheji gayi.
- Dhyan rahe: lookup is sandbox se hua tha, jo India mein nahi hai. AWS ELB DNS geo-based nahi hota aur Cloudflare anycast IP sab jagah same rehte hain, isliye result bharose layak hai (andaza). Phir bhi India ke VM se dobara check karna hai.

### 1.2 Table

| Host | Kaam (source) | DNS chain | IPv4 (10 Nov 2026) | IPv6? | Owner (RDAP / AWS ranges) |
|---|---|---|---|---|---|
| `api-hft.upstox.com` | Place, modify, cancel order (v2 aur v3) [S8][S9] | CNAME `prod-udapi-order-gw-rust-ngav2-1525346829.ap-south-1.elb.amazonaws.com` (TTL 60s) | 3.6.248.196, 13.232.55.50, 3.6.181.237 | Haan, 3 AAAA (2406:da1a:8e4:54xx::) | "AMAZON-BOM / Amazon Data Services India". AWS ranges: **ap-south-1, EC2** [S2][S3] |
| `wsfeeder-api.upstox.com` | Market data feed v3 ka WebSocket (authorize ka redirect) [S11][S12] | CNAME `p-market-data-feeder-v-ext-ngav2-723600359.ap-south-1.elb.amazonaws.com` | 13.200.45.37, 13.204.56.13, 13.203.147.246 | Haan, 3 AAAA | AMAZON-BOM / Amazon Technologies. AWS ranges: **ap-south-1, EC2** [S2][S3] |
| `api.upstox.com` | Auth, non-order APIs, feed authorize, kill switch, exit-all, portfolio WS [S8][S11][S14][S15] | CNAME `api.upstox.com.cdn.cloudflare.net` | 104.18.40.77, 172.64.147.179 | Haan | **Cloudflare, Inc.** (CLOUDFLARENET) [S3] |
| `login.upstox.com`, `ws-api.upstox.com` | Login / WS (naam se andaza) | `*.cdn.cloudflare.net` | Upar wale Cloudflare IP | Haan | Cloudflare [S3] |
| `upstox.com` (website) | Website | Seedha A record | 13.32.205.x | – | **CloudFront** (AWS GLOBAL) [S2][S3] |
| NS records | – | `awsdns-*` (Route 53) | – | – | AWS [S1] |

### 1.3 WebSocket feed ka raasta
- **Authorize endpoint:** `GET /feed/market-data-feed/authorize` [S11]. Official page par sirf path hai. Host `api.upstox.com` SDK docs ke "All URIs are relative to https://api.upstox.com" se pata chalta hai [S12]. Version v3 hai (community se: `/v3/feed/market-data-feed/authorize`).
- Iska response `authorized_redirect_uri` deta hai. Official example mein host chhupa hua hai: `wss://xyz.upstox.com/market-data-feeder/v3/upstox-developer-api/feeds?requestId=…&code=…`. Yeh URL ek hi baar chalta hai [S11].
- Asli redirect host **`wsfeeder-api.upstox.com`** hai. Yeh community post (9 Sep 2025) mein dikha [S12b] aur upar ka DNS bhi isse match karta hai.
- Portfolio/order-update stream: `wss://api.upstox.com/v2/feed/portfolio-stream-feed?...` [S14]. Matlab order updates Cloudflare se hokar aate hain (ek extra hop, andaza).
- Limits: Standard plan mein **2 connection per user**, Upstox Plus mein 5 [S13].

### 1.4 Iska matlab
- Order aur tick data dono AWS ap-south-1 mein hain. Isliye **Bot ka AWS ap-south-1 mein hona sabse sahi hai** (andaza: same region = sabse kam RTT).
- ELB ke 3 IP shayad 3 alag AZ mein hain. Iska andaza IPv6 ke 3 subnets (…5400, …5401, …5403) se lagaya, yeh verify nahi hua. Probe har IP ko alag se naapega taaki pata chale kaunsa "same-AZ" hai.
- IP kabhi **hardcode mat karna**. TTL 60s hai aur ELB ke IP badalte rehte hain.
- api-hft aur wsfeeder dono par **AAAA (IPv6) records hain**. Agar VM par IPv6 on hua to order IPv6 se ja sakta hai aur registered IPv4 se match nahi karega, phir UDAPI1154 reject aayega. Isliye Bot par IPv6 egress band rakhna hai (Section 5).
- **Latency par public data:**
  - Upstox staff ke mutabik ~45 ms "internal order execution" hai: order call server tak pahunchne se exchange ack tak (MohitGolecha, 9 Jun 2025) [S24]. v3 response mein `metadata.latency` (ms) aata hai, example value 30 hai [S9].
  - Ek forum reply mein likha hai: "AWS Mumbai par latency kaafi kam hogi" (user shrini, staff confirm nahi) [S25].
  - **Kisi cloud se Upstox tak ka independent RTT measurement nahi mila. Verify nahi hua.**

---

## 2. Upstox Static IP niyam

| Niyam | Kya likha hai | Source | Status |
|---|---|---|---|
| Kitne IP | Har **user** ko 1 Primary (zaroori) + 1 Secondary (optional, backup/failover ke liye) | [S5][S6][S7] | Official |
| User ya app level | Get/Update API docs: "user level, kisi bhi OAuth client se token ho, same IP lagu". Purana community post "2 IP per API App" kehta tha. | [S5][S6][S4] | Official docs: user level |
| Kitni baar badal sakte | "**once per calendar week**" (error UDAPI1185) | [S5][S6] | Official |
| Badalne ka asar | Saare **access token invalid** ho jaate hain. OAuth dobara karna padta hai. | [S5][S6] | Official |
| IPv4/IPv6 | "standard IPv4 or IPv6 notation" chalta hai. Primary aur Secondary alag hone chahiye (UDAPI1184). | [S5][S7] | Official. Community guide mein sirf IPv4 likha hai [S4]. |
| Kaunse API restricted | Place, Modify, Cancel, Multi Place/Cancel, GTT, **Exit All Positions**. Holdings, positions, funds, candles restricted nahi. | [S7] | Official |
| Galat IP par error | UDAPI1154: "Access to this API is blocked due to static IP restrictions". Error mein origin IP bhi aata hai (11 Apr 2026). | [S4b] | Community, staff post |
| Sharing | Ek IP sirf ek customer ka hai. Family sharing 7 May 2026 se allowed (staff). | [S7][S10] | Official + staff |
| Alag provider ke IP | Official page par **kuch nahi likha**. Staff post AWS EIP, GCP static, Azure reserved, DO floating IP aur ISP static IP sabko valid option batata hai. | [S4b] | **Verify nahi hua** (mana nahi hai, par saaf allowed bhi nahi likha) |
| Secondary par ek saath orders | Docs: "Orders will be accepted only from these registered IPs". Ek user ne Apr 2026 mein bataya ki secondary par UDAPI1154 aaya, jawab nahi mila. | [S6b][S4b] | **Verify nahi hua** |
| **Single app rule** | "From 1 April, only a single active API app per user will be allowed… additional apps… deleted" (VINIT, Team Upstox, 27 Mar 2026) | [S10] | Staff announcement |
| Market orders | Market orders band, MPP default on (31 Mar 2026) | [S10b] | Staff announcement |
| 10 OPS | 10 orders/second se upar ho to exchange algo registration chahiye | [S7][S10b] | Official |
| Kill switch API | `api.upstox.com/v2/user/kill-switch`. Segment disable se pehle saari positions band honi chahiye. Disable par open orders auto-cancel. **12 ghante ka cooling** period. 10 Apr 2026 se effective. | [S15] | Official. Static IP restriction lagti hai ya nahi, **verify nahi hua**. |
| Token | Naya token banane se purana invalid hota hai. Token 3:30 AM tak valid rehta hai. | [S26] | Community, **verify nahi hua** (official) |

**Project ke liye matlab:**
- Bot ko **Primary** IP milega (AWS Elastic IP). Pehredaar ko **Secondary** (GCP static IP). Dashboard aur probe VM ko koi IP register nahi karna.
- Pehredaar ka sabse zaroori kaam "Exit All Positions" hai, aur woh IP-restricted hai [S7]. Isliye Secondary IP Pehredaar ke liye zaroori hai.
- Single-app rule [S10] aur naye token se purana invalid hone ki community report [S26] milkar dikhate hain ki **Pehredaar ka "alag app/alag token" plan shayad nahi chalega**. Bot aur Pehredaar ko ek hi app ka token share karna padega. Yeh D2 mein tay karna hai aur Upstox support se confirm karna hai.
- IP hafte mein ek baar hi badal sakte hain. Isliye cloud aisa chahiye jahan static IP **naye machine par shift ho sake**. AWS Elastic IP region-scoped hai aur "remap to another instance" ho jaata hai [S20]. Matlab AZ fail ho to nayi machine doosre AZ mein bana kar wahi IP laga sakte hain, Upstox par kuch nahi badalna padega.

---

## 3. Shortlist table

Saare price on-demand Linux ke hain. Mahina = 730 ghante (andaza; GCP page bhi 730 use karta hai). INR rate 1 USD = ₹93.94 hai: ECB reference 9 Nov 2026, USD 1.1193/EUR aur INR 105.1435/EUR ka cross rate [S60]. Yeh andaza hai. Asli bill par GST alag lagega [S61].

### 3A. Compute aur price

| # | Provider / region | Upstox (AWS ap-south-1) se doori | Instance (exact) | vCPU type | $/ghanta | $/mahina | ₹/mahina (andaza) |
|---|---|---|---|---|---|---|---|
| 1 | **AWS ap-south-1 Mumbai** [S16][S17] | Same region | **c8g.xlarge** 4 vCPU, 8 GiB (Bot) | Graviton4, **1 vCPU = 1 physical core** (threads/core = 1) [S18] | 0.10796 | 78.81 | 7,403 |
| | | | c8g.large 2 vCPU, 4 GiB (Pehredaar/probe) | Same | 0.05398 | 39.41 | 3,702 |
| | | | c7g.xlarge / c7g.large | Graviton3, physical core [S18] | 0.0982 / 0.0491 | 71.69 / 35.84 | 6,734 / 3,367 |
| | | | c7i.xlarge (x86 plan B) | Intel, 2 thread/core [S18] | 0.1785 | 130.31 | 12,240 |
| | | | c6a.xlarge (x86 sasta) | AMD, 2 thread/core [S18] | 0.0935 | 68.25 | 6,412 |
| | | | t4g.small 2 vCPU, 2 GiB (Dashboard) | **Burstable** | 0.0112 | 8.18 | 768 |
| 2 | **GCP asia-south1 Mumbai** (zones a, b, c) [S28][S33] | Alag provider, same shahar | **c4a-standard-2** 2 vCPU, 8 GiB | Axion: "SMT is not supported. Each vCPU is equivalent to an entire core" [S31] | 0.093388 | 68.17 | 6,404 |
| | | | c4a-highcpu-4 4 vCPU, 8 GiB | Same | 0.157576 | 115.03 | 10,806 |
| | | | e2-small (Dashboard) | Shared-core (andaza: burstable) | 0.02012 | 14.69 | 1,380 |
| 3 | **Azure Central India** (**Pune**, 3 AZ) [S36][S40] | Alag provider, alag shahar | **D2ps_v6** 2 vCPU, 8 GiB | Cobalt 100: "entire physical core for each vCPU" [S38] | 0.0462 | 33.73 | 3,168 |
| | | | D4ps_v6 4 vCPU, 16 GiB | Same | 0.0924 | 67.45 | 6,336 |
| | | | F4as_v6 (x86 AMD) | verify nahi hua | 0.176 | 128.48 | 12,069 |
| 4 | **E2E Networks** (data centre Delhi aur Chennai; **Mumbai nahi**) [S44][S46] | Alag shahar, door | **SDC3-4.30GB** 4 dedicated vCPU, 30 GB | "Dedicated vCPUs" [S44] | 0.099 | 72.43 | 6,804 |
| | | | C3.8GB 4 vCPU, 8 GB | Dedicated nahi likha | 0.049 | 35.64 | 3,348 |
| 5 | **Akamai (Linode) Mumbai** `ap-west` aur `in-bom-2` (Chennai `in-maa` bhi) [S50][S52] | Alag provider, same shahar | Dedicated 4GB (g6-dedicated-2): 2 vCPU, 4 GB, 80 GB disk, 4 TB transfer | Dedicated CPU. SMT hai ya nahi, verify nahi hua. | 0.054 | 36.00 | 3,382 |
| | | | Dedicated 8GB (g6-dedicated-4): 4 vCPU | Same | 0.108 | 72.00 | 6,763 |
| 6 | **DigitalOcean BLR1** (Bangalore; **Mumbai region nahi hai**) [S55][S56] | Alag shahar | c-2: 2 vCPU, 4 GiB, 4 TB transfer | CPU-Optimized (dedicated) | 0.0625 | 42.00 | 3,945 |
| | | | c-4: 4 vCPU, 8 GiB | Same | 0.125 | 84.00 | 7,891 |
| 7 | **Oracle OCI Mumbai** (price list global) [S58] | Alag provider | E5.Flex 1 OCPU (= 2 x86 vCPU) + 8 GB | 1 OCPU = 1 physical core [S59] | 0.046 | 33.58 | 3,154 |

Note: Community mein "DigitalOcean Mumbai region" ki salah di gayi thi [S4]. DO ki official list mein India ka sirf BLR1 (Bangalore) hai [S55].

### 3B. Platform kasauti (criteria)

| Provider | Static/public IPv4 charge | Alag zone ka option | Uptime SLA (official) | Snapshot / backup | DDoS (default) | Clock sync service | Egress (internet bahar) | Steal / noisy-neighbour risk (andaza) |
|---|---|---|---|---|---|---|---|---|
| AWS | $0.005/IP/ghanta (in-use ya idle, dono) = $3.65/mahina [S19]. EIP region-scoped, remap ho sakta hai, default quota 5/region [S20] | Mumbai mein 3 AZ (aps1-az1/2/3) [S22] | Region (multi-AZ) 99.99%, ek instance 99.5% [S23] | EBS snapshot $0.05/GB-mahina, gp3 disk $0.0912/GB-mahina (Mumbai) [S17] | Shield Standard: "automatically… at no additional cost", L3/L4 [S27] | Time Sync `169.254.169.123`. Precision-time placement group (C8g supported, sab commercial regions, free) se PHC `/dev/ptp_ena`, microsecond-level [S21] | Pehle 100 GB/mahina free (sab regions mila kar), phir $0.1093/GB. Same region mein AZ ke beech $0.01/GB [S16b][S17b] | **Kam**: C8g/C7g mein SMT nahi. Burstable sirf t4g. |
| GCP | In-use static/ephemeral IP $0.005/ghanta. Reserved par unused $0.01/ghanta [S29] | 3 zone; C4A teeno zone mein [S33] | Ek instance 99.9%, multi-zone 99.99% [S30] | Snapshot $0.052/GiB-mahina, Hyperdisk Balanced $0.083/GiB-mahina (Mumbai) [S34] | Verify nahi hua | `metadata.google.internal` NTP, leap smear. Bahar ke NTP mix na karne ki salah [S32] | Standard tier pehle 200 GiB free. Premium tier ka Mumbai rate verify nahi hua (table mein $0.12/GiB dikha) [S29] | **Kam**: C4A mein SMT nahi [S31]. Live migration pause verify nahi hua. |
| Azure (Pune) | Standard static IPv4 $0.005/ghanta [S39] | 3 AZ [S36] | 2+ VM alag AZ mein 99.99%. Single VM Premium SSD ke saath 99.9%, Standard SSD ke saath 99.5% [S37] | P4 Premium SSD (32 GiB) $5.28/mahina. Snapshot ke do rate dikhe ($0.05 aur $0.132/GB), kaunsa lagega verify nahi hua [S39] | Infrastructure-level protection default; paid tier alag [S41] | Host PTP `/dev/ptp_hyperv` + chrony `refclock PHC` [S42] | 100 GB free, phir $0.12/GB (MS network) ya $0.11 (internet routing). Inter-AZ $0.01/GB [S39] | Kam (physical core). **Par memory-preserving maintenance mein VM 30 second tak pause ho sakta hai** [S42] |
| E2E | Reserved IP $3/mahina [S44] | Delhi aur Chennai DC; zone concept verify nahi hua | 99.9% (credit = extra din) [S45] | Snapshot $0.05/GB/mahina [S44] | Verify nahi hua | Verify nahi hua | Compute egress price page par nahi mila, verify nahi hua | SDC3 kam. C3 medium-high (dedicated nahi likha). |
| Akamai | Kam se kam 1 IPv4 included hai ya nahi, verify nahi hua | AZ nahi. Mumbai mein do alag DC (`ap-west`, `in-bom-2`) [S50] | 99.99% (GA), credit ticket se [S53] | Backup price verify nahi hua | Basic free (sirf secondary source), verify nahi hua [S54] | Cloud NTP service verify nahi hua | 4–5 TB plan mein included, overage $0.005/GB [S52] | Kam-medium (andaza) |
| DigitalOcean | Reserved IP free agar droplet se juda ho; khaali pada ho to $5/mahina [S57] | Sirf BLR1 | Har droplet 99.99% [S56b] | Verify nahi hua | Verify nahi hua | Verify nahi hua | Plan mein 4–5 TB | Kam-medium (andaza) |
| OCI | Verify nahi hua | Mumbai mein AD/FD ki ginti verify nahi hua | Verify nahi hua | Block volume $0.0255/GB-mahina + perf units [S58] | Verify nahi hua | Verify nahi hua | APAC: pehle 10 TB free, phir $0.025/GB [S58] | Verify nahi hua |

**Steal time kya hai:** `/proc/stat` mein "steal" woh samay hai jab hypervisor ne CPU kisi doosre VM ko de diya [S62]. Probe ise naapega.

### 3C. Latency budget ke liye public numbers

| Item | Number | Source |
|---|---|---|
| Doori ka rule | "~1 ms round-trip per 100 km" (rough) | AWS blog, 25 Oct 2024 [S63] |
| AWS AZ ki doori | Saare AZ ek doosre se "within 100 km". Koi ms number nahi diya. | [S22b] |
| GCP zones | Sirf "low-latency network connections" likha hai, number nahi | [S33] |
| Azure Central India | **Pune** mein hai (Mumbai nahi). Andaza: 1–2 ms+ extra RTT, verify nahi hua. | [S36] |
| E2E (Delhi/Chennai), DO (Bangalore) | Andaza: doori ke hisaab se ~8–12 ms+ RTT. **Bot ke liye theek nahi.** Verify nahi hua. | doori rule [S63] |
| Upstox ke andar | ~30–45 ms (call server tak pahunche se exchange ack tak) | [S24][S9] |
| Zerodha Kite users (Upstox nahi) | AWS Mumbai se order placement 100–130 ms (forum) | sirf reference, Upstox ke liye verify nahi hua |

---

## 4. Kharcha table (3 machine, mahina, tarikh: 10 Nov 2026)

Assumptions (andaza):
- Disk: Bot 30 GB, baaki 20 GB.
- Har disk ka ek snapshot rakha.
- Egress free tier ke andar rahega, kyunki bot sirf orders bhejta hai aur market data inbound hai.
- GST alag hai. AWS India 18% GST lagata hai [S61]. GCP/Azure India ka GST verify nahi hua.

### Combo (i): sab AWS ap-south-1, alag AZ

| Machine | Instance | Compute | IPv4 | Disk | Snapshot | Kul $ |
|---|---|---|---|---|---|---|
| Bot (aps1-az A) | c8g.xlarge | 78.81 | 3.65 | 2.74 (30 GB gp3) | 1.50 | **86.70** |
| Pehredaar (aps1-az B) | c8g.large | 39.41 | 3.65 | 1.82 | 1.00 | **45.88** |
| Dashboard (aps1-az C) | t4g.small | 8.18 | 3.65 | 1.82 | 1.00 | **14.65** |
| **Kul** | | | | | | **$147.23 ≈ ₹13,830** (18% GST ke saath ≈ ₹16,319) |

### Combo (ii): Bot + Dashboard AWS par, Pehredaar doosre provider par

| Machine | Instance | Kul $/mahina |
|---|---|---|
| Bot (AWS) | c8g.xlarge | 86.70 |
| Dashboard (AWS) | t4g.small | 14.65 |
| **Pehredaar, option A: GCP asia-south1** | c4a-standard-2: 68.17 + IP 3.65 + Hyperdisk 20 GiB 1.66 + snapshot 1.04 | **74.52** (Hyperdisk IOPS/throughput charge verify nahi hua) |
| **Kul (ii-A)** | | **$175.87 ≈ ₹16,521** (18% GST lage to ≈ ₹19,494) |
| Pehredaar, option B: Azure Central India | D2ps_v6: 33.73 + IP 3.65 + P4 5.28 + snapshot ~1.6 | 44.26, kul **$145.61 ≈ ₹13,677** |
| Pehredaar, option C: Akamai Mumbai 2 | Dedicated 4GB, disk aur transfer included | 36.00, kul **$137.35 ≈ ₹12,902** (IPv4 aur backup charge verify nahi hua) |

**Trial / probe ka kharcha (1 hafta = 168 ghante, andaza):**

| VM | Kharcha |
|---|---|
| AWS c8g.xlarge | ~$19.61 |
| GCP c4a-standard-2 | ~$16.91 |
| Azure D2ps_v6 | ~$9.82 (ya Akamai ~$9.07) |
| **Kul** | **~$46 ≈ ₹4,300** |

---

## 5. Settings recommendation (har ek ka ek-line kyun)

**OS**
- **Ubuntu 24.04 LTS (minimal cloud image).** Standard security support May 2029 tak hai [S64]. 26.04 LTS bhi Apr 2026 mein aa chuka hai [S64], lekin 24.04 zyada purana aur parkha hua hai. 26.04 par baad mein jaayenge (andaza). 26.04.1 aaya ya nahi, verify nahi hua.
- System clock UTC par rakho, app mein IST dikhao. Kyun: log aur exchange time mein confusion nahi hoga.

**Hardening**
- **SSH sirf key se**: `PasswordAuthentication no`, `PermitRootLogin no`. Kyun: password guess karke koi andar na aa sake.
- Behtar yeh hai ki **public SSH port band** ho aur cloud ka console tunnel use ho (AWS SSM / GCP IAP / Azure Bastion). Inke docs verify nahi hue. Kyun: internet se koi login port khula hi na rahe.
- **Firewall default-deny inbound**: cloud security group + `ufw`/nftables. Bot par koi inbound port nahi. Dashboard par sirf 443. Kyun: kam darwaaze, kam khatra.
- **fail2ban** sirf tab lagao jab SSH bahar khula ho. Kyun: baar-baar galat login karne waale IP ban ho jaayein.
- **Unattended security updates** on rakho, par **`Automatic-Reboot` off**. Reboot sirf weekend ya 16:00 IST ke baad, haath se. Kyun: market ke beech machine reboot nahi honi chahiye. Ubuntu docs: [S65] (page redirect hua, content verify nahi hua).
- **IPv6 egress band** (subnet IPv4-only, ya `net.ipv6.conf.all.disable_ipv6=1`). Kyun: api-hft/wsfeeder par AAAA records hain, aur order unregistered IPv6 se nikla to reject hoga [S1][S7]. AWS EIP waise bhi IPv6 support nahi karta [S20].
- Bot machine par Dashboard ya web server nahi, aur Dashboard machine par broker token nahi. Kyun: website hack ho to bhi order na lag sake.

**CPU aur memory**
- `c8g.xlarge` = 4 physical core [S18]. Plan (andaza, probe se test karna hai):
  - core 0: OS, IRQ, chrony, ssh
  - core 1: market-data WS reader
  - core 2: strategy + order
  - core 3: logging/DB
- Kernel cmdline: `isolcpus=domain,managed_irq,1-2 nohz_full=1-2 rcu_nocbs=1-2 irqaffinity=0`. Kyun: core 1 aur 2 par kernel ka kaam aur scheduler ki bheed na aaye. Domain isolation reboot ke bina wapas nahi hota [S66].
- systemd: bot service mein `CPUAffinity=1 2`, baaki services `CPUAffinity=0 3`. Kyun: bot apne core par tika rahe. Docs: [S67] (page 503 tha, content verify nahi hua).
- Debug ke liye `taskset` bhi kaam karta hai.
- **Swap off** (`swapoff -a` + fstab se hatao). Kyun: memory disk par gayi to latency achanak badh jaati hai. Iske badle memory monitoring rakho, aur non-critical services par `MemoryMax`.
- **tuned profile `network-latency`**. Isme `latency-performance` + THP never + `busy_poll=50` + `tcp_fastopen=3` + `numa_balancing=0` aata hai [S68]. Kyun: tez aur ek jaisa network response. Ubuntu par tuned ka bootloader hissa khud apply hoga ya nahi, verify nahi hua. `tsc=reliable` ARM par lagu nahi hota.

**NIC / IRQ**
- ENA (AWS) ki IRQs core 0 par rakho. `irqbalance` band karo ya isolated cores ko ban karo. Kyun: network interrupt strategy wale core ko na roke.
- Queue count (`ethtool -L`) probe se tay karna hai (andaza).

**Time (chrony)**
- **AWS Bot:**
  - `server 169.254.169.123 prefer iburst minpoll 4 maxpoll 4` [S21]
  - Precision-time placement group mein: `refclock PHC /dev/ptp_ena poll 0 delay 0.000010 prefer` [S21] (ENA driver ≥ 2.10 + `phc_enable=1` chahiye. Ubuntu kernel mein yeh hai ya nahi, verify nahi hua.)
  - Kyun: microsecond-level sahi time, aur log/tick timestamps bharose layak.
- **GCP:** sirf `server metadata.google.internal prefer iburst`. Koi bahar ka NTP mix nahi [S32].
- **Azure:** `refclock PHC /dev/ptp_hyperv poll 3 dpoll -2 offset 0 stratum 2` + `makestep 1.0 -1` [S42].
- Smeared (NTP) aur non-smeared (PHC) source leap second ke time par mix mat karo [S21b]. Kyun: leap second par dono alag time dikhayenge.

**DNS**
- `systemd-resolved` caching on, TTL ka izzat karo (ELB TTL 60s). Kyun: IP badle to bot naye IP par jaaye. DNS lookup ka samay probe mein naapo.

---

## 6. Probe script ka DESIGN (abhi code nahi; Upstox par auth nahi)

**Machines:** 3 trial VM, 5 trading din (Mon–Fri; NSE holiday list R-c se check karna).

| VM | Instance | Kyun |
|---|---|---|
| V1 | AWS ap-south-1 `c8g.xlarge` (precision-time PG mein) | Bot ka candidate |
| V2 | GCP asia-south1 `c4a-standard-2` | Pehredaar ka candidate |
| V3 | Azure Central India `D2ps_v6` (ya Akamai `in-bom-2` Dedicated 4GB) | Plan B |

Bonus (andaza): V1 ko pehle 2 din aps1-az1 mein aur agle 3 din doosre AZ mein chalao, taaki AZ ka fark dikhe.

**Kab:** 09:00–15:30 IST. Ismein 09:15–09:20 (open) aur 15:20–15:30 (close) alag bucket honge.

**Har X = 10 second** par, har target host ke **har resolve hue IP** ke liye ek sample:
1. DNS time: local cache (systemd-resolved) aur uncached (direct VPC resolver), dono.
2. TCP connect time (SYN se ACK tak, `perf_counter_ns`).
3. TLS handshake time (SNI = hostname). Sirf handshake, phir close. **Koi HTTP request, token ya WS upgrade nahi.**
4. `chronyc -c tracking` se offset, RMS offset, stratum aur reference.
5. `/proc/stat` delta se steal%, CPU% aur load1.

- **Targets:** `api-hft.upstox.com:443`, `wsfeeder-api.upstox.com:443`, `api.upstox.com:443`.
- **Har din ke sample:** 6.5 ghante × 360 = 2,340 per host per IP-set. 5 din mein ~11,700 sample. p99.9 ke liye kaafi hai (andaza: ~12 sample tail mein).
- 10 s isliye rakha ki Upstox ya Cloudflare isse abuse na samjhe (andaza). Probe shuru karne se pehle Upstox community se poochh lo (verify nahi hua).

**CSV schema** (file `probe_<vm>_<YYYYMMDD>.csv`):

| Column | Type | Kya hai |
|---|---|---|
| ts_utc | ISO8601 ns | Sample ka samay |
| ts_ist | ISO8601 | IST samay |
| vm_id | text | V1 / V2 / V3 |
| provider | text | aws / gcp / azure / akamai |
| zone | text | Jaise aps1-az1, asia-south1-b |
| instance_type | text | VM ka type |
| target_host | text | Kaunsa Upstox host |
| target_ip | text | Kaunsa IP |
| ip_family | 4/6 | IPv4 ya IPv6 |
| dns_cached_us | int | Cache se DNS ka samay |
| dns_uncached_us | int | Bina cache DNS ka samay |
| tcp_connect_us | int | TCP connect ka samay |
| tls_handshake_us | int | TLS handshake ka samay |
| tls_version | text | TLS version |
| cipher | text | Cipher |
| cert_valid | bool | Certificate sahi tha ya nahi |
| error | text, khaali = ok | Kya galat hua |
| chrony_offset_ns | int | Clock offset |
| chrony_rms_ns | int | RMS offset |
| chrony_stratum | int | Stratum |
| chrony_ref | text | Time source |
| steal_pct | float | Steal % |
| cpu_pct | float | CPU % |
| load1 | float | 1-min load |
| bucket | text | open / normal / close |

**Summary** (`summary_<YYYYMMDD>.csv`): har vm × host × IP × metric × bucket ke liye count, p50, p90, p99, p99.9, max, error_rate aur sabse lamba gap (s).

**Pass/fail kasauti** (andaza; pehle hafte ke data ke baad D2 mein final hogi):

| Metric | Bot VM (V1) | Pehredaar VM |
|---|---|---|
| TCP connect: api-hft aur wsfeeder | p50 ≤ 2 ms, p99 ≤ 5 ms, p99.9 ≤ 20 ms | p99 ≤ 20 ms |
| TLS handshake | p99 ≤ 15 ms | p99 ≤ 40 ms |
| Error rate | ≤ 0.1% | ≤ 0.5% |
| Lagatar fail | Koi 30 s se lamba nahi | Koi 30 s se lamba nahi |
| \|chrony offset\| | p99 ≤ 100 µs (PHC ke saath) ya ≤ 1 ms | p99 ≤ 5 ms |
| Steal | p99 ≤ 1%, max ≤ 5% | max ≤ 10% |

- **Faisla:** jis AZ/IP ka p99 sabse kam ho, Bot wahin jaayega.
- Agar AWS V1 fail ho jaaye, to Section 7 ka Plan B.

---

## 7. Final recommendation: "Yeh khareedo, yeh wajah, yeh plan B"

**Pehle measure karo, phir khareedo.** Pehle Section 6 ka probe (~₹4,300, 1 hafta) chalao, aur Upstox se 3 sawaal confirm karo:
1. Single-app rule ke saath Pehredaar token kaise lega?
2. Secondary IP se aur doosre provider ke IP se orders ek saath chalte hain ya nahi?
3. Kill switch par static IP lagta hai ya nahi?

| Machine | Yeh khareedo | Wajah | Plan B |
|---|---|---|---|
| **Bot** | **AWS ap-south-1 `c8g.xlarge`**, precision-time placement group mein, **Elastic IP = Upstox Primary IP**, AZ probe se chuno | Upstox ke order aur feed ELB isi region mein hain [S1][S2]. 4 physical core se pinning aasaan [S18]. PHC clock free [S21]. EIP AZ fail hone par nayi machine par shift ho jaata hai, Upstox IP badalna nahi padta [S20]. $78.81/mahina. | x86 chahiye (library ARM par na chale) to `c7i.xlarge` ($130.31) ya `c6a.xlarge` ($68.25, SMT wala). CPU kam pade to `c8g.2xlarge` (price verify nahi hua). |
| **Pehredaar** | **GCP asia-south1 `c4a-standard-2`** + static external IP = **Upstox Secondary IP** | Alag company aur alag account, isliye AWS account ya billing ki galti dono ko ek saath nahi giraegi. Mumbai mein hai. Physical core [S31]. Internal NTP [S32]. SLA 99.9% [S30]. $74.52/mahina. | (B1) Azure Central India `D2ps_v6` ($44.26; Pune; 30 s maintenance pause ka risk [S42]). (B2) Akamai `in-bom-2` Dedicated 4GB ($36; zone/NTP service nahi). (B3) Agar Upstox ne doosre provider ka IP mana kiya: AWS `c8g.large` doosre AZ mein (combo i). |
| **Dashboard** | **AWS `t4g.small`** teesre AZ mein, **broker token ke bina**, sirf 443 khula, malik login + 2FA | Burstable bhi chalega kyunki latency zaroori nahi. Sasta: $14.65. Bot machine se alag hai. | GCP `e2-small` ($14.69 compute). Cloudflare Tunnel (public IP ke bina) ek option hai, verify nahi hua. |

- **Kul (combo ii-A): ~$176/mahina ≈ ₹16,500**, GST alag.
- Agar budget tight hai to **combo (i) ~$147 ≈ ₹13,830** bhi theek hai. Pehredaar alag AZ mein hoga, par ek hi provider ka khatra rahega.
- Dhyan rahe: agar AWS Mumbai poora down hua to Upstox ke apne servers (wahin hosted) bhi shayad down honge (andaza). Isliye alag provider ka asli fayda **account/ops ki galti se bachav** hai, region outage se nahi.

---

## 8. "Verify nahi hua" list

1. `api.upstox.com` ka origin kahan hai (Cloudflare ke peeche). AWS Mumbai VM kaunse Cloudflare PoP par jaata hai (Mumbai BOM PoP maujood hai [S3b]).
2. Kisi bhi cloud se Upstox host tak ka asli RTT. Koi public measurement nahi mila.
3. ELB ke 3 IP kaunse AZ mein hain (IPv6 subnets se andaza).
4. Secondary IP se orders, Primary ke saath ek hi samay par, chalte hain ya nahi (ek community report mein UDAPI1154 aaya tha).
5. Primary aur Secondary alag provider ke ho sakte hain ya nahi. Mana nahi kiya gaya, par saaf allowed bhi nahi likha.
6. Single-app rule ke baad Pehredaar ko token kaise milega. Ek app ke multiple token. Naye token se purana invalid hona (sirf community source).
7. Kill switch API par static IP restriction lagti hai ya nahi.
8. Upstox ka disaster recovery (AWS ap-south-1 down ho to kya hoga).
9. Probe ka 10 s interval Upstox/Cloudflare ko theek lagega ya nahi.
10. GCP: Premium tier egress ka exact Mumbai rate, Hyperdisk baseline IOPS free hai ya nahi, default DDoS, C4A par live-migration pause. n2d ke Mumbai rate ajeeb dikhe, isliye use nahi kiye.
11. Azure: snapshot ka asli rate, Pune–Mumbai ka RTT, maintenance pause kitni baar hota hai.
12. E2E: INR price (page ne USD dikhaya), Mumbai DC (docs mein sirf Delhi/Chennai), compute egress, NTP, DDoS.
13. Akamai: IPv4 included hai ya nahi, official DDoS doc, NTP service, Dedicated CPU par SMT, backup price.
14. DigitalOcean: DDoS, backup price, NTP.
15. OCI: Mumbai mein AD/FD, SLA, IP charge, Ampere A1 price, DDoS.
16. Ubuntu kernel mein ENA PHC (`phc_enable`) support. tuned ka bootloader hissa Ubuntu par. 26.04.1 release.
17. GCP/Azure India par GST. AISPL vs AWS India entity ka naam.
18. Inter-AZ / inter-zone RTT ke official numbers (AWS/GCP ne number nahi diya).
19. Ubuntu unattended-upgrades page aur systemd.exec page ka content (fetch fail hua). Settings general practice par based hain.
20. ARM64 par project ki saari libraries chalengi ya nahi (R-e benchmark ke baad).

---

## 9. Sources (sab "dekha: 10 Nov 2026")

| # | Kya | URL |
|---|---|---|
| S1 | DNS lookup (Google DoH + python socket), 10 Nov 2026 | https://dns.google/resolve?name=api-hft.upstox.com&type=A (aur baaki hosts) |
| S2 | AWS ip-ranges.json (createDate 2026-11-09-14-47-05) | https://ip-ranges.amazonaws.com/ip-ranges.json |
| S3 | ARIN RDAP (104.18.40.77, 172.64.147.179, 13.232.55.50, 13.200.45.37, 3.6.248.196, 13.203.147.246, 13.204.56.13, 13.32.205.88) | https://rdap.arin.net/registry/ip/13.232.55.50 |
| S3b | Cloudflare status, India PoPs (Mumbai BOM) | https://www.cloudflarestatus.com/api/v2/components.json |
| S4 | Upstox community: Static IP Setup Guide (Mar–Apr 2026) | https://community.upstox.com/t/static-ip-setup-guide-for-api-traders/14683 |
| S4b | Upstox community: Static IP requirement (staff, 29 Jul 2025 – 11 Apr 2026) | https://community.upstox.com/t/important-update-static-ip-requirement-for-api-order-placement-effective-soon/10485 |
| S5 | Upstox docs: Update Static IPs | https://upstox.com/developer/api-documentation/update-app-static-ips/ |
| S6 | Upstox announcement: Static IP APIs (10 Apr 2026) | https://upstox.com/developer/api-documentation/announcements/static-ip-apis/ |
| S6b | Upstox appendix: My Apps support for algo circular | https://upstox.com/developer/api-documentation/appendix/my-apps-support-for-algo-trading-circular/ |
| S7 | Upstox announcement: Algo trading circular | https://upstox.com/developer/api-documentation/announcements/algo-trading-circular/ |
| S8 | Upstox announcement: Enhanced URL (api-hft) | https://upstox.com/developer/api-documentation/announcements/enhanced-url/ |
| S9 | Upstox docs: Place Order V3 (metadata.latency) | https://upstox.com/developer/api-documentation/v3/place-order/ |
| S10 | Upstox community: SEBI/Exchange mandates, single app (27 Mar 2026) | https://community.upstox.com/t/important-new-sebi-exchange-mandates-for-api-trading-effective-1st-april-2026/14822 |
| S10b | Upstox community: Regulatory changes now live (31 Mar 2026) | https://community.upstox.com/t/important-update-regulatory-changes-for-api-and-algo-trading-are-now-live/14874 |
| S11 | Upstox docs: Market Data Feed Authorize V3 | https://upstox.com/developer/api-documentation/get-market-data-feed-authorize-v3/ |
| S12 | Upstox Python SDK: WebsocketApi (base URL) | https://github.com/upstox/upstox-python/blob/master/docs/WebsocketApi.md |
| S12b | Upstox community: wsfeeder-api redirect URL (9 Sep 2025) | https://community.upstox.com/t/issue-with-live-market-data-feed-for-websocke/11432 |
| S13 | Upstox docs: Market data feed v3 (limits) | https://upstox.com/developer/api-documentation/v3/get-market-data-feed/ |
| S14 | Upstox docs: Portfolio stream feed | https://upstox.com/developer/api-documentation/get-portfolio-stream-feed/ |
| S15 | Upstox announcement: Kill Switch API | https://upstox.com/developer/api-documentation/announcements/kill-switch-api/ |
| S15b | Upstox docs: Exit All Positions | https://upstox.com/developer/api-documentation/example-code/orders/exit-all-positions/ |
| S16 | AWS EC2 on-demand price data, Mumbai Linux (publication 2026-11-07) | https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Mumbai)/Linux/index.json (page: https://aws.amazon.com/ec2/pricing/on-demand/) |
| S16b | AWS EC2 pricing page (100 GB free egress) | https://aws.amazon.com/ec2/pricing/on-demand/ |
| S17 | AWS Price List bulk CSV ap-south-1 (gp3 $0.0912, snapshot $0.05; Last-Modified 7 Nov 2026) | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/ap-south-1/index.csv |
| S17b | AWS Price List: Data Transfer ap-south-1 (publication 2026-11-03) | https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AWSDataTransfer/current/ap-south-1/index.json |
| S18 | AWS CPU options per instance type | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/cpu-options-supported-instances-values.html |
| S19 | AWS VPC pricing (public IPv4) | https://aws.amazon.com/vpc/pricing/ |
| S20 | AWS Elastic IP docs | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/elastic-ip-addresses-eip.html |
| S21 | AWS Time Sync / precision-time / PHC | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configure-ec2-ntp.html |
| S21b | AWS set-time (leap smear notes) | https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/set-time.html |
| S22 | AWS Availability Zones list (aps1-az1..3) | https://docs.aws.amazon.com/global-infrastructure/latest/regions/aws-availability-zones.html |
| S22b | AWS Regions & AZ page ("within 100 km") | https://aws.amazon.com/about-aws/global-infrastructure/regions_az/ |
| S23 | AWS Compute SLA (updated 25 May 2022) | https://aws.amazon.com/compute/sla/ |
| S24 | Upstox community: <45ms latency clarification (9 Jun 2025) | https://community.upstox.com/t/re-9351107-clarification-on-achieving-45ms-latency-with-upstox-api/9453/2 |
| S25 | Upstox community: WebSocket latency thread (19 May 2025) | https://community.upstox.com/t/websocket-latency-much-higher-than-expected-1000-1500ms-vs-claimed-30-50ms/9103 |
| S26 | Upstox community: token invalidation (search result) | https://community.upstox.com/t/upstox-api-access-token/8942 |
| S27 | AWS Shield | https://aws.amazon.com/shield/ |
| S28 | GCP compute pricing, general-purpose (embedded asia-south1 tables) | https://cloud.google.com/products/compute/pricing/general-purpose |
| S29 | GCP network pricing (IP, egress) | https://cloud.google.com/vpc/network-pricing |
| S30 | GCP Compute Engine SLA | https://cloud.google.com/compute/sla |
| S31 | GCP general-purpose machines (C4A SMT note) | https://docs.cloud.google.com/compute/docs/general-purpose-machines |
| S32 | GCP configure NTP | https://docs.cloud.google.com/compute/docs/instances/configure-ntp |
| S33 | GCP regions & zones (asia-south1 a/b/c) | https://cloud.google.com/compute/docs/regions-zones |
| S34 | GCP disk & snapshot pricing (asia-south1) | https://cloud.google.com/compute/disks-image-pricing |
| S36 | Azure regions list (Central India = Pune, 3 AZ; West India = Mumbai, no AZ) | https://learn.microsoft.com/en-us/azure/reliability/regions-list |
| S37 | Microsoft SLA for Online Services (WW, English, November 2026) | https://www.microsoft.com/licensing/docs/documents/download/OnlineSvcsConsolidatedSLA(WW)(English)(November_2026)(CR).docx |
| S38 | Azure Dpsv6 series | https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/dpsv6-series |
| S39 | Azure Retail Prices API (centralindia: VMs, IP, disks, bandwidth) | https://prices.azure.com/api/retail/prices |
| S40 | Azure Linux VM pricing (reference page) | https://azure.microsoft.com/en-in/pricing/details/virtual-machines/linux/ |
| S41 | Azure DDoS Protection overview | https://learn.microsoft.com/en-us/azure/ddos-protection/ddos-protection-overview |
| S42 | Azure Linux time sync (PTP, 30 s pause) | https://learn.microsoft.com/en-us/azure/virtual-machines/linux/time-sync |
| S44 | E2E Networks pricing | https://www.e2enetworks.com/pricing |
| S45 | E2E SLA | https://www.e2enetworks.com/policies/service-level-agreement |
| S46 | E2E docs home ("Data centres in Delhi and Chennai") | https://docs.e2enetworks.com/ |
| S50 | Akamai/Linode regions API (ap-west, in-bom-2, in-maa) | https://api.linode.com/v4/regions |
| S52 | Akamai CPU pricing + types API | https://www.akamai.com/cloud/pricing/cpu , https://api.linode.com/v4/linode/types |
| S53 | Akamai compute SLA (v1.2, effective 27 Feb 2026) | https://www.akamai.com/legal/sla-compute |
| S54 | Linode DDoS (secondary/community) | https://www.akamai.com/community/questions/40468/ddos-on-linodes |
| S55 | DigitalOcean regional availability | https://docs.digitalocean.com/platform/regional-availability/ |
| S56 | DigitalOcean droplet pricing | https://www.digitalocean.com/pricing/droplets |
| S56b | DigitalOcean CPU Droplet SLA (updated 3 Jun 2025) | https://www.digitalocean.com/sla/cpu-droplets |
| S57 | DigitalOcean reserved IP pricing (verified 26 Oct 2026) | https://docs.digitalocean.com/products/networking/reserved-ips/details/pricing/ |
| S58 | Oracle price list API (lastUpdated 2026-11-02) | https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/?currencyCode=USD |
| S59 | Oracle compute pricing (OCPU = physical core) | https://www.oracle.com/cloud/compute/pricing/ |
| S60 | ECB euro reference rates (9 Nov 2026) | https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml |
| S61 | AWS India tax help (GST 18%) | https://aws.amazon.com/tax-help/india/ |
| S62 | proc_stat(5) man page (steal) | https://man7.org/linux/man-pages/man5/proc_stat.5.html |
| S63 | AWS blog: Wavelength latency (25 Oct 2024) | https://aws.amazon.com/blogs/industries/lower-access-latency-for-your-apps-with-aws-wavelength-and-our-telco-partners/ |
| S64 | Ubuntu release cycle | https://ubuntu.com/about/release-cycle |
| S65 | Ubuntu automatic updates (redirect; content verify nahi hua) | https://ubuntu.com/server/docs/how-to/software/automatic-updates/ |
| S66 | Linux kernel parameters (isolcpus) | https://raw.githubusercontent.com/torvalds/linux/master/Documentation/admin-guide/kernel-parameters.txt |
| S67 | systemd.exec (CPUAffinity; fetch 503, verify nahi hua) | https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html |
| S68 | tuned profiles (upstream repo) | https://github.com/redhat-performance/tuned/tree/master/profiles |
