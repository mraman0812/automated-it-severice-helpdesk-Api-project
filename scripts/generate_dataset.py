"""
Script to generate a rich, realistic IT Support Ticket dataset for training TF-IDF + Classifier models.
"""
import os
import csv
import random

CATEGORIES_DATA = {
    "Network": {
        "department": "Network Support",
        "subcategories": {
            "VPN": {
                "priority_dist": [("HIGH", 0.7), ("MEDIUM", 0.2), ("CRITICAL", 0.1)],
                "templates": [
                    ("Cannot connect to corporate VPN", "Unable to establish VPN connection from home. It says handshake failed or connection timed out."),
                    ("VPN disconnects every 10 minutes", "GlobalProtect / AnyConnect keeps dropping every few minutes disrupting remote desktop."),
                    ("VPN authentication failed", "Entering my credentials but VPN says authentication error even though password is correct."),
                    ("VPN client installation error", "When trying to install the Cisco VPN client on macOS, the installer throws error 1722."),
                    ("Cannot access internal git server through VPN", "VPN is connected with green status but I cannot ping or clone from gitlab.internal."),
                    ("VPN tunnel blocked by home ISP", "My ISP appears to be throttling UDP port 4500 and VPN won't establish tunnel."),
                    ("VPN certificate expired", "Error message says client certificate has expired and needs renewal from network admin."),
                    ("Pulse Secure VPN crashing on startup", "Whenever I launch the Pulse Secure VPN app on Windows 11, it crashes immediately."),
                    ("Remote access VPN speed extremely slow", "VPN connection is established but speeds are below 50 Kbps making it impossible to work."),
                    ("VPN routing issues with subnet", "Unable to access 10.200.x.x subnet while on corporate VPN.")
                ]
            },
            "WiFi": {
                "priority_dist": [("MEDIUM", 0.6), ("LOW", 0.2), ("HIGH", 0.2)],
                "templates": [
                    ("Unable to connect to office WiFi", "My laptop sees the Corp-WiFi SSID but fails to obtain an IP address via DHCP."),
                    ("Office WiFi keeps dropping connection", "The 5GHz WiFi in conference room 3B drops connections every few minutes."),
                    ("Guest WiFi password not working", "Visitors in our reception area cannot authenticate to Corp-Guest network."),
                    ("WiFi connected but no internet access", "Connected to WiFi with full signal bars, but browser says DNS resolution failed."),
                    ("Slow WiFi speeds on 4th floor", "Speed test shows under 2 Mbps across the entire marketing floor WiFi access points."),
                    ("WiFi adapter not recognized in laptop", "Windows Device Manager shows a yellow exclamation mark next to Intel WiFi 6 AX201."),
                    ("Certificate error when joining 802.1x WiFi", "Device prompts for RADIUS server certificate trust and refuses to connect."),
                    ("WiFi captive portal not appearing", "When connecting to the guest wireless network, the captive portal login page does not load.")
                ]
            },
            "Internet Connectivity": {
                "priority_dist": [("HIGH", 0.6), ("MEDIUM", 0.3), ("CRITICAL", 0.1)],
                "templates": [
                    ("No internet access on workstation", "Ethernet cable is plugged in, link lights are on, but cannot browse any websites."),
                    ("DNS lookup failed for external domains", "Can ping 8.8.8.8 directly by IP but cannot resolve google.com or office.com."),
                    ("Intermittent packet loss on office LAN", "Experiencing 25% packet loss when pinging local gateway 192.168.1.1."),
                    ("Ethernet port on wall plate not working", "Plugging into jack D-14 at desk 42 does not provide link light or IP address."),
                    ("High network latency in design studio", "Ping times to internal file server spiked to 600ms, impacting video editing.")
                ]
            },
            "DNS": {
                "priority_dist": [("MEDIUM", 0.5), ("HIGH", 0.4), ("CRITICAL", 0.1)],
                "templates": [
                    ("Internal DNS not resolving intranet portals", "Attempts to navigate to intranet.company.local result in DNS_PROBE_FINISHED_NXDOMAIN."),
                    ("Stale DNS records for staging server", "DNS still points to the old decommissioned IP address 10.0.5.21."),
                    ("Reverse DNS lookup failure", "Mail server is failing reverse PTR checks causing outgoing emails to bounce.")
                ]
            }
        }
    },
    "Hardware": {
        "department": "Hardware Support",
        "subcategories": {
            "Laptop": {
                "priority_dist": [("HIGH", 0.5), ("MEDIUM", 0.4), ("LOW", 0.1)],
                "templates": [
                    ("Laptop battery swollen and pushing touchpad", "The chassis of my ThinkPad is bulging and the trackpad cannot be clicked. Urgent safety hazard."),
                    ("Laptop screen cracked / black display", "Accidentally dropped backpack and the screen has rainbow lines and cracked LCD."),
                    ("Laptop won't power on at all", "Pressing power button produces no fan noise, charging LED doesn't light up."),
                    ("Laptop keyboard spacebar and enter key broken", "Several keys on the built-in keyboard are unresponsive or falling off."),
                    ("Laptop fan making loud grinding noise and overheating", "The cooling fan is rattling loudly and the CPU throttles to 0.4 GHz."),
                    ("Charger cable frayed and spark noticed", "The USB-C power adapter cable is frayed near the brick and needs replacement."),
                    ("Touchpad unresponsive on Dell Latitude", "Cursor doesn't move when using the trackpad; external USB mouse works fine.")
                ]
            },
            "Monitor": {
                "priority_dist": [("MEDIUM", 0.7), ("LOW", 0.2), ("HIGH", 0.1)],
                "templates": [
                    ("External monitor flickering continuously", "Dell 27-inch monitor flickers black every 5 seconds over HDMI and DisplayPort."),
                    ("Second monitor not detected by docking station", "Laptop only outputs to built-in screen; external display says No Signal."),
                    ("Dead pixels line across display", "A vertical pink line has appeared down the center of my secondary screen."),
                    ("Monitor resolution stuck at 1024x768", "Display settings won't allow switching to native 2560x1440 resolution.")
                ]
            },
            "Printer": {
                "priority_dist": [("MEDIUM", 0.6), ("LOW", 0.3), ("HIGH", 0.1)],
                "templates": [
                    ("Floor 2 HP LaserJet paper jam error 13.00", "Paper is stuck in tray 2 and the printer display says Jam in Cartridge Area."),
                    ("Printer out of toner cartridge black", "Printing documents comes out faint and streaked. Need replacement black toner."),
                    ("Network printer offline in Windows print queue", "Sending print jobs to HR-Printer-01 sits in spooler status Offline."),
                    ("Printer leaving black smudge across pages", "Drum unit appears dirty, leaving horizontal stripes on every printed invoice.")
                ]
            },
            "Peripherals": {
                "priority_dist": [("LOW", 0.8), ("MEDIUM", 0.2)],
                "templates": [
                    ("Wireless mouse scroll wheel broken", "Logitech wireless mouse scroll wheel is spinning freely without scrolling."),
                    ("External USB keyboard typing double letters", "Keys chattering: typing 'e' produces 'ee' on the mechanical keyboard."),
                    ("Jabra headset microphone not capturing audio", "Can hear callers in Teams meeting but microphone picks up no sound."),
                    ("USB-C docking station ports not working", "USB flash drives plugged into dock front ports are not detected by Windows.")
                ]
            }
        }
    },
    "Software": {
        "department": "Software Support",
        "subcategories": {
            "Application Crash": {
                "priority_dist": [("HIGH", 0.6), ("MEDIUM", 0.3), ("CRITICAL", 0.1)],
                "templates": [
                    ("Excel crashing when opening financial report", "Opening large 50MB spreadsheet causes Excel to crash with Exception code 0xc0000005."),
                    ("AutoCAD freezing on startup splash screen", "AutoCAD 2024 hangs at 'Checking license...' and then terminates silently."),
                    ("Slack crashes every time a call starts", "Joining huddles in Slack causes the app to terminate immediately on Windows 11."),
                    ("Visual Studio Code memory leak and crash", "VS Code consumes 16 GB RAM within 30 minutes and freezes the operating system."),
                    ("Salesforce desktop plugin crashing Outlook", "Add-in for Salesforce causes Outlook to hang during startup in safe mode.")
                ]
            },
            "Software Installation": {
                "priority_dist": [("LOW", 0.7), ("MEDIUM", 0.3)],
                "templates": [
                    ("Requesting Python and Docker desktop installation", "Need local development tools installed on my workstation for new project."),
                    ("Please install Adobe Acrobat Pro", "I need to edit and sign PDF contracts for clients; standard Reader is insufficient."),
                    ("NodeJS and Git installation approval", "Requesting admin privilege or Software Center deployment of Node.js v20 LTS."),
                    ("Install Postman for API testing", "Require Postman desktop client for testing microservices endpoints."),
                    ("Install Zoom client for upcoming client presentation", "Software Center installation of Zoom failed with error code 1603.")
                ]
            },
            "License Issue": {
                "priority_dist": [("MEDIUM", 0.6), ("HIGH", 0.3), ("LOW", 0.1)],
                "templates": [
                    ("Microsoft 365 license expired notification", "Word and PowerPoint are showing 'Unlicensed Product' banner and disabled editing."),
                    ("JetBrains IntelliJ IDEA license key expired", "License server says no floating licenses available for IntelliJ Ultimate."),
                    ("Figma enterprise seat license request", "Need editor access to team design files in Figma workspace."),
                    ("Tableau Desktop license activation error", "Tableau activation server unreachable error when activating license key.")
                ]
            },
            "Update Issue": {
                "priority_dist": [("MEDIUM", 0.6), ("HIGH", 0.3), ("LOW", 0.1)],
                "templates": [
                    ("Windows 11 update stuck at 74% loop", "Laptop has been rebooting and reverting update KB5034441 for 2 hours."),
                    ("Chrome browser update failed with error 7", "Chrome cannot update to latest security release on enterprise workstation."),
                    ("macOS Sonoma update bricked display output", "After applying OS patch, secondary monitors are no longer detected.")
                ]
            }
        }
    },
    "Account & Access": {
        "department": "IT Helpdesk",
        "subcategories": {
            "Password Reset": {
                "priority_dist": [("MEDIUM", 0.6), ("LOW", 0.3), ("HIGH", 0.1)],
                "templates": [
                    ("Forgot Active Directory / Windows password", "Returned from vacation and cannot recall my domain password. Locked out of PC."),
                    ("Password reset link expired or invalid", "Self-service password reset portal says security questions are not configured."),
                    ("ERP system password expired", "SAP / Oracle login states credentials have expired and requires IT admin reset."),
                    ("Temporary password not working on first login", "IT provided a temporary password but portal says incorrect credentials."),
                    ("Unable to reset password via SMS OTP", "OTP code for password reset is not arriving on my registered mobile device.")
                ]
            },
            "Login Problem": {
                "priority_dist": [("HIGH", 0.6), ("MEDIUM", 0.3), ("CRITICAL", 0.1)],
                "templates": [
                    ("Account locked after 3 invalid attempts", "My domain account is locked out across all workstations and SSO services."),
                    ("SSO login loop on Okta / Azure AD", "Attempting to login to internal portal keeps redirecting back to login screen in a loop."),
                    ("User account disabled message on Windows login", "Screen shows 'Your account has been disabled. Please see your system administrator.'"),
                    ("Cannot login to workstation with smart card", "PIN is entered correctly but smart card reader shows error 0x80090016.")
                ]
            },
            "MFA": {
                "priority_dist": [("HIGH", 0.7), ("MEDIUM", 0.3)],
                "templates": [
                    ("New phone, need MFA Authenticator reset", "I upgraded my smartphone and lost Microsoft Authenticator app 2FA tokens."),
                    ("MFA push notifications not received on mobile", "Authenticator app is not popping up push requests to approve login."),
                    ("YubiKey hardware token not recognized for MFA", "FIDO2 security key fails when tapping for multi-factor authentication."),
                    ("MFA phone number change request", "Changed phone number and cannot receive SMS verification codes for corporate portal.")
                ]
            },
            "Access Request": {
                "priority_dist": [("LOW", 0.5), ("MEDIUM", 0.4), ("HIGH", 0.1)],
                "templates": [
                    ("Request access to Finance shared network drive", "Need read/write permissions to \\fileserver\\finance\\quarterly-reports for audit."),
                    ("Need access to GitHub organization repository", "Starting on Project Apollo, please add my GitHub user to backend engineering team."),
                    ("Jira and Confluence project space permissions", "Need edit permissions in Jira project board SRE and team documentation space."),
                    ("AWS IAM console read-only access request", "Requesting AWS sandbox account access for cloud architecture evaluation.")
                ]
            }
        }
    },
    "Email": {
        "department": "Email Support",
        "subcategories": {
            "Outlook Problem": {
                "priority_dist": [("MEDIUM", 0.6), ("HIGH", 0.3), ("LOW", 0.1)],
                "templates": [
                    ("Outlook stuck on 'Loading Profile' splash", "Outlook desktop client does not open past the profile loading screen."),
                    ("Outlook search indexing not returning emails", "Searching for customer emails in Outlook returns zero results or incomplete list."),
                    ("Outlook calendar appointments disappeared", "Shared team calendar is not syncing and recurring meetings have vanished."),
                    ("Outlook OST data file corrupt error", "Error message: 'The file C:\\Users\\user\\AppData\\outlook.ost cannot be accessed.'"),
                    ("Outlook disconnected from Exchange server", "Status bar in Outlook constantly displays Disconnected or Trying to connect.")
                ]
            },
            "Email Not Sending": {
                "priority_dist": [("HIGH", 0.6), ("MEDIUM", 0.3), ("CRITICAL", 0.1)],
                "templates": [
                    ("Emails stuck in Outbox and not sending", "Outgoing messages with or without attachments stay in Outbox indefinitely."),
                    ("Bounce back error 550 Relaying denied", "Sending email to client domains results in NDR error 5.7.1 Access denied."),
                    ("Outgoing emails blocked by spam filter", "Sent emails are bouncing with SPF/DKIM validation failure message."),
                    ("Cannot send email to distribution list", "Getting error: 'You don't have permission to send to this distribution group.'")
                ]
            },
            "Email Not Receiving": {
                "priority_dist": [("HIGH", 0.7), ("MEDIUM", 0.2), ("CRITICAL", 0.1)],
                "templates": [
                    ("Not receiving external emails from clients", "Colleagues can email me internally, but no external emails are arriving today."),
                    ("Mailbox full quota exceeded error", "Cannot receive new incoming emails because mailbox has reached 50 GB limit."),
                    ("Important client email delayed by 8 hours", "Incoming emails are queuing up in mail gateway with severe delivery latency."),
                    ("Emails going directly to Junk / Spam folder", "Legitimate internal communication from HR is being routed to Spam folder.")
                ]
            },
            "Spam": {
                "priority_dist": [("MEDIUM", 0.6), ("HIGH", 0.3), ("LOW", 0.1)],
                "templates": [
                    ("Receiving multiple targeted phishing emails", "Several staff members received email asking to verify credentials urgently."),
                    ("Spam filter letting through malicious invoice attachments", "Spoofed emails with zip attachments bypassing Office 365 spam filters."),
                    ("Suspicious CEO gift card request email", "Email purporting to be from CEO asking for employee cell phone numbers.")
                ]
            }
        }
    },
    "Security": {
        "department": "Security",
        "subcategories": {
            "Phishing": {
                "priority_dist": [("HIGH", 0.6), ("CRITICAL", 0.3), ("MEDIUM", 0.1)],
                "templates": [
                    ("Clicked suspicious link in unexpected email", "I inadvertently clicked on a link in an email claiming to be Microsoft password reset."),
                    ("Entered credentials on fake login page", "Realized after submitting password that the URL was secure-login-verify.xyz, not company domain."),
                    ("Phishing campaign report: fake payroll bonus notification", "Received email claiming HR bonus with macro-enabled Excel document attached."),
                    ("Spear phishing targeting executive assistant", "Attacker attempting wire transfer authorization using spoofed CFO email header.")
                ]
            },
            "Malware": {
                "priority_dist": [("CRITICAL", 0.6), ("HIGH", 0.4)],
                "templates": [
                    ("Antivirus pop-up: Trojan.Win32 detected and quarantined", "Windows Defender alerted about suspicious executable found in Temp directory."),
                    ("Ransomware note displayed on desktop background", "Files have .locked extension and a text file demands cryptocurrency payment. Disconnected from LAN."),
                    ("Workstation displaying weird popups and opening browsers", "Browser windows opening automatically to gambling and ad sites every 30 seconds."),
                    ("Unknown PowerShell script executing in background", "EDR software alerted on encoded PowerShell command execution under user profile.")
                ]
            },
            "Suspicious Login": {
                "priority_dist": [("CRITICAL", 0.5), ("HIGH", 0.4), ("MEDIUM", 0.1)],
                "templates": [
                    ("Alert: Login to my corporate account from Russia / Unknown location", "Received Microsoft security alert about successful login from unfamiliar IP address."),
                    ("Multiple failed login attempts during midnight hours", "Security log shows 400 failed login attempts against my username."),
                    ("Session hijacked on corporate portal", "Activity log indicates active session while I was asleep and laptop was powered off.")
                ]
            },
            "Security Incident": {
                "priority_dist": [("CRITICAL", 0.7), ("HIGH", 0.3)],
                "templates": [
                    ("Lost company laptop on public transit", "Left encrypted MacBook Pro on the train this morning. Need remote wipe immediately."),
                    ("USB thumb drive found in parking lot plugged in by mistake", "An employee plugged an unknown USB drive found outside into their desktop."),
                    ("Confidential customer data sent to wrong external email address", "Mistakenly autofilled incorrect recipient and sent quarterly client PII spreadsheet.")
                ]
            }
        }
    },
    "Server / Infrastructure": {
        "department": "Infrastructure",
        "subcategories": {
            "Server Down": {
                "priority_dist": [("CRITICAL", 0.8), ("HIGH", 0.2)],
                "templates": [
                    ("Production Kubernetes cluster node kernel panic", "Worker node 04 crashed with kernel panic; pods evicting to remaining nodes."),
                    ("Core API server unresponsive with HTTP 502/504 errors", "NGINX reverse proxy is throwing 502 Bad Gateway for all client traffic to main backend."),
                    ("Production Linux server unreachable via SSH or ping", "Webserver prod-web-01 stopped responding to health checks 10 minutes ago."),
                    ("Active Directory domain controller replication failed", "DC02 is failing Kerberos authentication and replication sync with primary DC01."),
                    ("Hyper-V host hardware purple screen of death", "Host server running 15 virtual machines crashed due to memory parity error.")
                ]
            },
            "Database Issue": {
                "priority_dist": [("CRITICAL", 0.7), ("HIGH", 0.3)],
                "templates": [
                    ("PostgreSQL primary database connection pool exhausted", "Application logs show 'FATAL: remaining connection slots are reserved for non-replication superuser connections'."),
                    ("Production database query deadlocks causing timeouts", "Multiple transactions on orders table deadlocking and aborting checkout flows."),
                    ("Database disk space utilization reached 98%", "Postgres WAL archive directory is filling up rapidly; less than 2 GB remaining."),
                    ("Database replica lag exceeded 30 minutes", "Read replica in secondary region is falling behind master causing stale reads.")
                ]
            },
            "Storage": {
                "priority_dist": [("HIGH", 0.6), ("MEDIUM", 0.3), ("CRITICAL", 0.1)],
                "templates": [
                    ("SAN storage volume degraded on LUN 3", "Storage array controller reporting failed drive in RAID 6 group."),
                    ("Shared network drive \\\\nas01\\projects is out of space", "Users cannot save files to corporate project storage; disk quota exceeded."),
                    ("NFS mount stale file handle on backup server", "Backup script failing because NFS export becomes unreachable during sync.")
                ]
            },
            "Backup": {
                "priority_dist": [("HIGH", 0.5), ("MEDIUM", 0.4), ("CRITICAL", 0.1)],
                "templates": [
                    ("Nightly automated database backup failed", "Veeam / pg_dump job terminated with exit code 1; snapshot could not be committed."),
                    ("Requesting file restoration from tape backup", "Need accidentally deleted folder /var/www/legacy restored from last Friday's backup."),
                    ("Offsite cloud backup replication sync error", "AWS S3 glacier lifecycle replication job timed out with network error.")
                ]
            },
            "System Outage": {
                "priority_dist": [("CRITICAL", 0.9), ("HIGH", 0.1)],
                "templates": [
                    ("Total datacenter power loss / UPS failure in Server Room B", "Main power feed tripped; backup generator engaged but UPS A did not switch cleanly."),
                    ("Company-wide intranet and ERP completely inaccessible", "All employees in North America region unable to access ERP, HR portal, or intranet."),
                    ("Core switch stack failure in MDF room", "Cisco core switch stack member 1 went offline cutting off all VLAN routing.")
                ]
            }
        }
    }
}

VARIATIONS = [
    ("", ""),
    ("Please assist urgently. ", " This is blocking my daily tasks."),
    ("Need immediate help with this. ", " Occurred right after rebooting."),
    ("FYI for the helpdesk team. ", " Multiple teammates are experiencing this as well."),
    ("Issue started this morning. ", " Restarting the system did not resolve the problem."),
    ("Urgent assistance required: ", " Error code was captured in screenshot."),
    ("Help needed: ", " Kindly look into this as soon as possible."),
    ("Escalation: ", " Impacting ongoing customer deliverables."),
]


def pick_priority(dist):
    rand = random.random()
    cumulative = 0.0
    for prio, weight in dist:
        cumulative += weight
        if rand <= cumulative:
            return prio
    return dist[0][0]


def generate_dataset(output_path: str, count_multiplier: int = 4):
    random.seed(42)
    rows = []

    for category, cat_data in CATEGORIES_DATA.items():
        dept = cat_data["department"]
        for subcat, subcat_data in cat_data["subcategories"].items():
            prio_dist = subcat_data["priority_dist"]
            templates = subcat_data["templates"]

            for title_base, desc_base in templates:
                # Add base sample
                base_prio = pick_priority(prio_dist)
                rows.append({
                    "title": title_base,
                    "description": desc_base,
                    "category": category,
                    "subcategory": subcat,
                    "priority": base_prio,
                    "department": dept
                })

                # Add variations
                for m in range(count_multiplier):
                    prefix, suffix = random.choice(VARIATIONS)
                    var_title = f"{prefix}{title_base}".strip()
                    var_desc = f"{desc_base}{suffix}".strip()
                    var_prio = pick_priority(prio_dist)
                    rows.append({
                        "title": var_title,
                        "description": var_desc,
                        "category": category,
                        "subcategory": subcat,
                        "priority": var_prio,
                        "department": dept
                    })

    # Shuffle rows
    random.shuffle(rows)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "description", "category", "subcategory", "priority", "department"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} tickets in {output_path}")


if __name__ == "__main__":
    out = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "training", "tickets.csv")
    generate_dataset(out, count_multiplier=5)
