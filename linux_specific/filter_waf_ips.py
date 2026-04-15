import ipaddress
import argparse
import urllib.request
import json


def main():
    parser = argparse.ArgumentParser(
        description="Filter out IPs belonging to known WAF ranges (Cloudflare, Google CDN, Fastly)"
    )
    parser.add_argument(
        "-i", "--input",
        default="urls.final.txt",
        help="Input file containing IP addresses (default: urls.final.txt)"
    )
    parser.add_argument(
        "-o", "--output",
        default="ips_to_scan.txt",
        help="Output file for filtered IPs (default: ips_to_scan.txt)"
    )
    args = parser.parse_args()

    with open(args.input) as f, open(args.output, "w") as out:
        for line in f:
            ip_str = line.strip()
            if not ip_str:
                continue
            try:
                real_ip = ip_str.split(":")[0]
                ip = ipaddress.ip_address(real_ip)
                if not any(ip in net for net in waf_networks):
                    out.write(ip_str + "\n")
            except ValueError:
                pass


# WAF ranges
waf_ranges = {
    "private_ranges": [
        "10.0.0.0/8",
        "192.168.0.0/16",
        "172.16.0.0/12",
    ],
    # https://techdocs.akamai.com/origin-ip-acl/docs/update-your-origin-server
    "akamai": [
        "2.16.0.0/13",
        "23.0.0.0/12",
        "23.192.0.0/11",
        "23.32.0.0/11",
        "95.100.0.0/15",
        "184.24.0.0/13"
    ],
}

try:
    with urllib.request.urlopen("https://ip-ranges.amazonaws.com/ip-ranges.json") as response:
        aws_data = json.loads(response.read().decode('utf-8'))
        aws_ips = [item['ip_prefix'] for item in aws_data['prefixes'] if item['service'] == 'CLOUDFRONT']
        waf_ranges["aws_cloudfront"] = aws_ips
except Exception as e:
    print(f"[!] Error fetching AWS CloudFront IPs: {e}")

# Fetch Cloudflare IPv4 ranges (Official API)
try:
    with urllib.request.urlopen("https://www.cloudflare.com/ips-v4") as response:
        cf_ipv4 = response.read().decode('utf-8').splitlines()
        waf_ranges["cloudflare"].extend(cf_ipv4)
except Exception as e:
    print(f"[!] Error fetching Cloudflare IPs: {e}")

# Fetch Fastly IP ranges (Official API)
try:
    with urllib.request.urlopen("https://api.fastly.com/public-ip-list") as response:
        fastly_data = json.loads(response.read().decode('utf-8'))
        waf_ranges["fastly"].extend(fastly_data['addresses'])
except Exception as e:
    print(f"[!] Error fetching Fastly IPs: {e}")


# Combine all WAF ranges
all_waf_ranges = []
for ranges in waf_ranges.values():
    all_waf_ranges.extend(ranges)

waf_networks = [ipaddress.ip_network(r) for r in all_waf_ranges]



if __name__ == "__main__":
    main()
