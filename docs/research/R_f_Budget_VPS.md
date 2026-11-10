# R-f: ₹1,500 mahine ka server plan (malik ka niyam, 10 Nov 2026)

**Tarikh:** 10 Nov 2026 · **Kisne:** Claude Code (khud jaancha, subagent nahi) · Faisla `docs/02_Tech_Decisions.md` Section D8 mein.

## Saar
1. Malik ka niyam: teeno server ka kharcha ₹1,500/mahina ke andar.
2. Bot: AWS Lightsail Mumbai, Linux $12 plan (2 vCPU, 2 GB, 60 GB, static IP shaamil, CPU baseline 20% prati vCPU). Lightsail usi AWS Mumbai region mein hai jahan Upstox ke order aur feed server hain (`R_a`).
3. Pehredaar aur Dashboard: Oracle Cloud Always Free (2 AMD micro, har ek mein 1 public IP). Khatra: idle machine delete ho sakti hai.
4. Plan B: Bot Lightsail $7 + Pehredaar Vultr Mumbai $5 + Dashboard Oracle Free (~₹1,330).
5. INR: $1 = ₹93.94 (ECB, 9 Nov 2026; `R_a` S60); GST 18% (AWS India, `R_a` S61; baaki par verify nahi hua).

## Kya dekha (sab 10 Nov 2026)

| Baat | Kya mila | Source |
|---|---|---|
| Lightsail Linux bundles (IPv4) | $5 (0.5 GB, 2 vCPU, 20 GB), $7 (1 GB, 2 vCPU, 40 GB), $12 (2 GB, 2 vCPU, 60 GB), $24 (4 GB, 2 vCPU, 80 GB). "Static IP address" har plan mein shaamil. Region suchi mein Asia Pacific (Mumbai); wahan transfer allowance aadha | https://aws.amazon.com/lightsail/pricing/ |
| Lightsail CPU baseline (prati vCPU) | $5: 5%, $7: 10%, $12: 20%, $24: 20% (29 Jun 2023 ke baad bani machines) | https://docs.aws.amazon.com/lightsail/latest/userguide/baseline-cpu-performance.html |
| AWS EC2 Mumbai sabse sasta | `t4g.nano` $0.0028/h, `t4g.micro` $0.0056/h, `t4g.small` $0.0112/h, `c7g.medium` $0.0245/h, `c8g.medium` $0.02699/h (price file publication 7 Nov 2026). Public IPv4 alag $0.005/h (`R_a` S19) | https://b0.p.awsstatic.com/pricing/2.0/meteredUnitMaps/ec2/USD/current/ec2-ondemand-without-sec-sel/Asia%20Pacific%20(Mumbai)/Linux/index.json |
| Oracle Always Free compute | Do `VM.Standard.E2.1.Micro` (1/8 OCPU + burst, 1 GB, "one VNIC with one public IP address", 50 Mbps). A1 Flex: 2 OCPU + 12 GB ke barabar. "You must create the Always Free compute instances in your home region." Idle: 7 din mein CPU p95 < 20%, network < 20% (A1 par memory < 20%) toh reclaim. 10 TB/mahina outbound free | https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm |
| Oracle reserved public IP free hai? | Page par zikr nahi | verify nahi hua |
| Oracle PAYG upgrade se idle reclaim se bachav | Sirf community post; official text nahi mila; upgrade par card authorization ka report | https://community.oracle.com/customerconnect/discussion/671904/reclamation-of-idle-compute-instances (verify nahi hua) |
| Vultr Mumbai (`bom`) | `vc2-1c-1gb` $5 (1 vCPU, 1 GB, 25 GB), `vc2-1c-2gb` $10 (1 vCPU, 2 GB, 55 GB). India regions: Bangalore, Mumbai, Delhi NCR. IPv4 shaamil hai ya nahi: verify nahi hua | https://api.vultr.com/v2/plans , https://api.vultr.com/v2/regions |
| Akamai (Linode) | Nanode 1 GB $5, Linode 2 GB $12 (region ke liye alag price nahi dikha) | https://api.linode.com/v4/linode/types |

## Verify nahi hua
- Lightsail par Amazon Time Sync / PHC; static IP ko nayi machine par le jaane ka exact tareeka; Lightsail par GST.
- Oracle Mumbai home region mein free micro ki capacity; public IP machine dobara banane par badalta hai ya nahi.
- Vultr par IPv4 aur GST.
- Bot ka asli RAM aur CPU (benchmark mein RAM naapi nahi gayi) — Paper Stage mein naapna.
