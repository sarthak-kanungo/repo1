# -*- coding: utf-8 -*-
"""Step specification: chapter, instructions and per-field callouts for each screen."""

CH_LOGIN   = "2. Login / Logout"
CH_PROFILE = "3. User Profile"
CH_CONTACT = "4. Contact Us"
CH_GATE    = "5. Gate In / Gate Out"
CH_AUTO    = "6. Auto Job Cards (Daily / Ten-Day)"
CH_ASSIGN  = "7. Assign Auto Job Cards"
CH_DCR     = "8. DCR Charging"

STEPS = [

# ---------------------------------------------------------------- 2. LOGIN
dict(ch=CH_LOGIN, screen="s01", title="Open the Application and Sign In",
     caption="Sign-in screen",
     bullets=[
       "Launch the JBM DMS Mobile Application by tapping the JBMDMS icon on your device.",
       "Enter your authorized username and password in the respective fields.",
       "Tap SIGN IN to authenticate.",
     ],
     note="Access is subject to the credentials and permissions configured by your administrator.",
     drop=[(168,1807)],
     extra=[
       ("JBM branding — confirms you are on the correct application", (370,725,460,210), "L"),
       ("SIGN IN TO CONTINUE — screen heading", (350,1040,500,75), "L"),
       ("Username — your authorized employee code (mandatory)", (165,1183,875,125), "L"),
       ("Password — masked while you type (mandatory)", (165,1367,875,125), "R"),
       ("Show / hide password icon", (766,1392,104,92), "R"),
       ("FORGOT PASSWORD? — raise a reset request with your administrator", (633,1533,417,64), "R"),
       ("SIGN IN — authenticates you and opens the home page", (165,1800,875,130), "L"),
     ]),

dict(ch=CH_LOGIN, screen="s02", title="Access the Home Dashboard",
     caption="Home page with Quick Links",
     bullets=[
       "On successful authentication the mobile application home page opens.",
       "Use Quick Links to open any module you are authorized for.",
       "Tap the menu icon at the top-left to open the side navigation panel.",
     ],
     note="Only the modules enabled for your role are listed; the arrangement may differ by user.",
     drop="all",
     extra=[
       ("Menu icon — opens the side navigation panel", (48,248,84,84), "L"),
       ("Logged-in user name", (210,238,350,118), "L"),
       ("Dashboard icon", (1028,238,112,98), "R"),
       ("Vehicle banner — swipe to scroll", (108,483,1000,334), "L"),
       ("Quick Links — your authorized modules", (105,1013,415,100), "L"),
       ("AUTO JOB CARD LIST", (98,1220,1012,156), "R"),
       ("GATE IN/OUT", (98,1420,1012,156), "R"),
       ("ASSIGN AUTO JOB CARD", (98,1620,1012,156), "R"),
       ("AUTO JOB CARD INSPECTION", (98,1820,1012,156), "R"),
       ("DCR CHARGING", (98,2020,1012,156), "L"),
       ("VENDOR JOB CARD", (98,2220,1012,156), "L"),
       ("VEHICLEHISTORY", (98,2420,1012,156), "L"),
     ]),

dict(ch=CH_LOGIN, screen="s03", title="Open the Menu and Select Logout",
     caption="Side navigation panel",
     bullets=[
       "Tap the menu icon of the application.",
       "The side panel lists every module available to you, plus My Profile and Contact Us.",
       "Select LOGOUT at the bottom of the panel.",
     ],
     drop="all",
     extra=[
       ("Logged-in user name and employee code", (320,205,265,125), "L"),
       ("AUTO JOB CARD LIST", (55,400,850,95), "L"),
       ("GATE IN/OUT", (55,530,850,95), "L"),
       ("ASSIGN AUTO JOB CARD", (55,663,850,95), "L"),
       ("AUTO JOB CARD INSPECTION", (55,795,850,95), "R"),
       ("DCR CHARGING", (55,927,850,95), "R"),
       ("VENDOR JOB CARD", (55,1059,850,95), "R"),
       ("VEHICLEHISTORY", (55,1191,850,95), "R"),
       ("MY PROFILE — view your profile details", (55,1371,850,95), "L"),
       ("CONTACT US — JBM HQ contact details", (55,1473,850,95), "L"),
       ("LOGOUT — ends the session", (55,1633,850,102), "R"),
       ("App version and JBM branding", (110,2355,645,135), "R"),
     ]),

dict(ch=CH_LOGIN, screen="s04", title="Confirm the Logout",
     caption="Confirm Logout dialog",
     bullets=[
       "A confirmation dialog appears when you select Logout.",
       "Tap YES, LOG OUT to confirm; you are redirected to the login screen.",
       "Tap CANCEL to stay signed in and return to the home page.",
     ],
     note="After logging out your credentials are required again to access depot operations.",
     drop="all",
     extra=[
       ("CONFIRM LOGOUT — dialog title", (345,1190,510,70), "L"),
       ("Confirmation message", (215,1280,780,215), "L"),
       ("CANCEL — dismisses the dialog, session continues", (173,1562,416,127), "L"),
       ("YES, LOG OUT — ends the session and returns to the login screen", (624,1566,408,119), "R"),
       ("Home page remains behind the dialog until you confirm", (60,1800,1090,300), "R"),
     ]),

# -------------------------------------------------------------- 3. PROFILE
dict(ch=CH_PROFILE, screen="s05", title="View Your User Profile",
     caption="User Profile screen",
     bullets=[
       "Tap the menu icon and select My Profile to view your details.",
       "Review the profile parameters maintained for your user account.",
       "Tap the back arrow to return to the home page.",
     ],
     note="Only the parameters permitted by JBM can be updated; the rest are read-only.",
     drop="all",
     extra=[
       ("Back arrow — returns to the home page", (108,268,108,108), "L"),
       ("USER PROFILE — screen title", (248,278,432,92), "L"),
       ("Profile photo", (475,558,232,232), "L"),
       ("User name", (462,818,286,92), "L"),
       ("Role / designation", (438,913,324,62), "L"),
       ("USER CODE — your employee code and user type", (130,1073,1000,157), "R"),
       ("EMAIL ADDRESS", (130,1263,1000,157), "R"),
       ("CONTACT NUMBER", (130,1458,1000,157), "R"),
       ("DEPARTMENT", (130,1648,1000,157), "R"),
       ("LOCATION", (130,1838,1000,157), "R"),
     ]),

# -------------------------------------------------------------- 4. CONTACT
dict(ch=CH_CONTACT, screen="s06", title="View JBM HQ Contact Details",
     caption="Contact Us screen",
     bullets=[
       "Tap the menu icon and select Contact Us to view the details.",
       "Use the displayed address, contact number or email ID for assistance.",
       "Tap DROP US A LINE to open your mail application with the JBM mail ID.",
     ],
     note="Contact information is displayed from the data maintained by the authorized administrator / JBM team.",
     drop="all",
     extra=[
       ("Back arrow — returns to the home page", (108,268,108,108), "L"),
       ("CONTACT US — screen title", (248,278,412,92), "L"),
       ("Get in Touch — section heading", (123,993,474,77), "L"),
       ("Supporting text", (123,1098,902,132), "L"),
       ("Head Office — postal address", (128,1303,1002,192), "R"),
       ("Phone Number — HQ landlines", (128,1523,1002,182), "R"),
       ("Email Address — corporate communications mail ID", (128,1748,1002,202), "R"),
       ("DROP US A LINE — opens your mail application", (128,2008,947,147), "R"),
     ]),
]
