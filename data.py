"""data.py — Wittenberg University 2025-26 Academic Catalog
Sources:
  - 2025-26 Wittenberg Academic Catalog (PDF provided)
  - wittenberg.edu/academics/data-science/courses-requirements
  - wittenberg.edu/academics/finance/courses-requirements
  - wittenberg.edu/administration/registrar/general-academic-information
    → "The successful completion of 126 credits is a requirement for graduation."

KEY CORRECTIONS vs previous version:
  1. Total credits: 126 (not 124)
  2. Finance: 52 credits in major, 36 required + 4 related + 12 electives (per catalog)
  3. Data Science: 43 credits major (27 required + 16 electives)
  4. Finance choice group corrected: ECON 310 OR ECON 280 (Managerial Econ)
  5. Finance related dept: DATA 327 OR MATH 131 OR MATH 201 (not just MATH131)
  6. Finance electives: 2 from specified list + 1 from any ACCT/BUSN/ECON
  7. Data Science: Added DATA 280, COMP 275, ESCI 290, ESCI 291, PSYC 201, PSYC 202
  8. Data Science capstone: DATA 490 (2cr), DATA 491 (2cr), or DATA 499 (2cr)
  9. Added ECON 311 (Intermediate Macro) — required for Economics major, appears in DS electives
  10. BUSN 381 internship: 0-4 credits (can be 0 if approved alternative used)
  11. Added courses missing from old catalog: ACCT 226, BUSN 212, BUSN 340, BUSN 365,
      BUSN 460, ECON 311, COMP 275, DATA 280, ESCI 290, ESCI 291, PSYC 201, PSYC 202

Semester offering patterns are based on:
  - Catalog descriptions and course level/pattern (100/200 = both terms typical)
  - Upper-division (300/400) courses at small liberal arts schools typically
    alternate Fall/Spring or are annual
  - Business core (ACCT, ECON 200, BUSN 210) offered both semesters
  - Senior capstone/seminar courses: Spring only (typical at Wittenberg)
  - Where catalog specifies, that is used; otherwise best-estimate noted
"""

COURSES = {
    # ══════════════════════════════════════════════════════════════
    # CONNECTIONS CURRICULUM (Gen Ed) — all core-protected
    # ══════════════════════════════════════════════════════════════
    "WITT101": {
        "name": "Wittenberg Seminar (First Year)",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall"],  # FY seminar = Fall only
        "times": ["MWF 9:00-9:50am", "MWF 10:00-10:50am", "TTH 9:30-10:45am"],
        "desc": "Required first-year interdisciplinary seminar.",
        "core_protected": True,
    },
    "ENGL101": {
        "name": "Writing Seminar",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "MWF 11:00-11:50am", "TTH 11:00-12:15pm"],
        "desc": "Writing-intensive composition and rhetoric.",
        "core_protected": True,
    },
    "HIST101": {
        "name": "History (Connections)",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 1:00-2:15pm"],
        "desc": "Approved history course for Connections Curriculum.",
        "core_protected": True,
    },
    "ARTS101": {
        "name": "Fine Arts (Connections)",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["TTH 11:00-12:15pm", "MWF 2:00-2:50pm"],
        "desc": "Approved fine arts course for Connections Curriculum.",
        "core_protected": True,
    },
    "LANG101": {
        "name": "Foreign Language I",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "MWF 11:00-11:50am"],
        "desc": "First semester of a foreign language sequence.",
        "core_protected": True,
    },
    "LANG102": {
        "name": "Foreign Language II",
        "credits": 4, "type": "core", "prereqs": ["LANG101"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "MWF 11:00-11:50am"],
        "desc": "Second semester of a foreign language sequence.",
        "core_protected": True,
    },
    "SCI101": {
        "name": "Natural Science Lab (Connections)",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["TTH 8:00-9:15am", "MWF 2:00-2:50pm", "TTH 2:30-3:45pm"],
        "desc": "Approved lab science for Connections Curriculum.",
        "core_protected": True,
    },
    "RELI101": {
        "name": "Religion (Connections)",
        "credits": 4, "type": "core", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["TTH 12:00-1:15pm", "MWF 1:00-1:50pm"],
        "desc": "Religion or philosophy course for Connections Curriculum.",
        "core_protected": True,
    },

    # ══════════════════════════════════════════════════════════════
    # MATHEMATICS
    # ══════════════════════════════════════════════════════════════
    "MATH131": {
        "name": "Essentials of Calculus",
        "credits": 4, "type": "elective", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "MWF 10:00-10:50am", "TTH 9:30-10:45am"],
        "desc": "Calculus for business and social science applications.",
        "core_protected": False,
    },
    "MATH201": {
        "name": "Calculus I",
        "credits": 4, "type": "elective", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "MWF 11:00-11:50am"],
        "desc": "Limits, derivatives, and applications of differential calculus.",
        "core_protected": False,
    },
    "MATH202": {
        "name": "Calculus II",
        "credits": 4, "type": "elective", "prereqs": ["MATH201"],
        "offered": ["Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 1:00-2:15pm"],
        "desc": "Integration techniques, sequences, and series.",
        "core_protected": False,
    },
    "MATH210": {
        "name": "Introduction to Proofs",
        "credits": 4, "type": "elective", "prereqs": ["MATH201"],
        "offered": ["Fall"],
        "times": ["MWF 11:00-11:50am"],
        "desc": "Logic, sets, and proof-writing for upper-level mathematics.",
        "core_protected": False,
    },
    "MATH212": {
        "name": "Multivariable Calculus",
        "credits": 4, "type": "elective", "prereqs": ["MATH202"],
        "offered": ["Fall"],
        "times": ["MWF 10:00-10:50am"],
        "desc": "Calculus of several variables, partial derivatives, and multiple integrals.",
        "core_protected": False,
    },
    "MATH228": {
        "name": "Discrete Mathematics",
        "credits": 4, "type": "elective", "prereqs": ["MATH201"],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am", "MWF 1:00-1:50pm"],
        "desc": "Logic, combinatorics, graph theory, and discrete structures.",
        "core_protected": False,
    },
    "MATH261": {
        "name": "Linear Algebra",
        "credits": 4, "type": "elective", "prereqs": ["MATH202"],
        "offered": ["Spring"],
        "times": ["MWF 11:00-11:50am", "TTH 2:30-3:45pm"],
        "desc": "Vector spaces, matrices, eigenvalues, linear transformations.",
        "core_protected": False,
    },
    "MATH328": {
        "name": "Probability Theory",
        "credits": 4, "type": "elective", "prereqs": ["MATH202"],
        "offered": ["Spring"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Probability distributions, random variables, and limit theorems.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # COMPUTER SCIENCE
    # ══════════════════════════════════════════════════════════════
    "COMP150": {
        "name": "Computer Programming I",
        "credits": 4, "type": "major", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 1:00-1:50pm", "TTH 12:00-1:15pm", "TTH 3:00-4:15pm"],
        "desc": "Fundamentals of programming using Python.",
        "core_protected": False,
    },
    "COMP250": {
        "name": "Data Structures",
        "credits": 4, "type": "elective", "prereqs": ["COMP150"],
        "offered": ["Spring"],
        "times": ["MWF 2:00-2:50pm", "TTH 2:30-3:45pm"],
        "desc": "Arrays, linked lists, trees, graphs, sorting, and algorithm analysis.",
        "core_protected": False,
    },
    "COMP265": {
        "name": "Computer Organization",
        "credits": 4, "type": "elective", "prereqs": ["COMP150"],
        "offered": ["Fall"],
        "times": ["TTH 2:30-3:45pm"],
        "desc": "Computer architecture, assembly language, and low-level systems.",
        "core_protected": False,
    },
    "COMP275": {
        "name": "Web Development",
        "credits": 4, "type": "elective", "prereqs": ["COMP150"],
        "offered": ["Spring"],
        "times": ["MWF 1:00-1:50pm"],
        "desc": "HTML, CSS, JavaScript, and full-stack web application development.",
        "core_protected": False,
    },
    "COMP290": {
        "name": "Database Systems",
        "credits": 4, "type": "major", "prereqs": ["COMP150"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 1:00-1:50pm", "TTH 2:30-3:45pm"],
        "desc": "Database design, SQL, relational models, and data management.",
        "core_protected": False,
    },
    "COMP340": {
        "name": "Algorithms",
        "credits": 4, "type": "elective", "prereqs": ["COMP250", "MATH228"],
        "offered": ["Fall"],
        "times": ["MWF 11:00-11:50am"],
        "desc": "Algorithm design, complexity analysis, and optimization.",
        "core_protected": False,
    },
    "COMP350": {
        "name": "Software Engineering",
        "credits": 4, "type": "elective", "prereqs": ["COMP250"],
        "offered": ["Spring"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Software lifecycle, version control, testing, and team development.",
        "core_protected": False,
    },
    "COMP353": {
        "name": "Machine Learning",
        "credits": 4, "type": "elective", "prereqs": ["COMP250", "DATA227"],
        "offered": ["Spring"],
        "times": ["TTH 3:00-4:15pm"],
        "desc": "Supervised and unsupervised learning, model evaluation.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # DATA SCIENCE
    # ══════════════════════════════════════════════════════════════
    "DATA227": {
        "name": "Introductory Statistics",
        "credits": 4, "type": "major", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 11:00-11:50am", "TTH 9:30-10:45am", "MWF 1:00-1:50pm"],
        "desc": "Statistical reasoning, distributions, hypothesis testing, and regression.",
        "core_protected": False,
    },
    "DATA229": {
        "name": "Introduction to Data Science",
        "credits": 4, "type": "major", "prereqs": ["DATA227"],
        "offered": ["Spring"],
        "times": ["TTH 11:00-12:15pm", "MWF 2:00-2:50pm"],
        "desc": "Data wrangling, visualization, and exploratory analysis in R/Python.",
        "core_protected": False,
    },
    "DATA280": {
        "name": "Data Science Applications",
        "credits": 4, "type": "elective", "prereqs": ["DATA227"],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am"],
        "desc": "Applied data science methods across real-world domains.",
        "core_protected": False,
    },
    "DATA327": {
        "name": "Statistical Modeling",
        "credits": 4, "type": "major", "prereqs": ["DATA227"],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am", "MWF 10:00-10:50am"],
        "desc": "Regression, ANOVA, and applied statistical modeling.",
        "core_protected": False,
    },
    "DATA337": {
        "name": "Data Mining",
        "credits": 4, "type": "elective", "prereqs": ["DATA229"],
        "offered": ["Spring"],
        "times": ["MWF 2:00-2:50pm"],
        "desc": "Pattern discovery, clustering, and classification on large datasets.",
        "core_protected": False,
    },
    "DATA380": {
        "name": "Advanced Data Analytics",
        "credits": 4, "type": "elective", "prereqs": ["DATA327", "DATA229"],
        "offered": ["Fall"],
        "times": ["MWF 1:00-1:50pm"],
        "desc": "Advanced predictive analytics, time series, and big data methods.",
        "core_protected": False,
    },
    # Capstone options — 2 credits each; student needs at least 2 credits from this group
    "DATA490": {
        "name": "Data Science Capstone",
        "credits": 2, "type": "major", "prereqs": ["DATA229", "DATA327"],
        "offered": ["Spring"],
        "times": ["TTH 9:30-11:45am"],
        "desc": "Team-based capstone research project presented to faculty panel.",
        "core_protected": True,
    },
    "DATA491": {
        "name": "Data Science Internship Capstone",
        "credits": 2, "type": "major", "prereqs": ["DATA229"],
        "offered": ["Fall", "Spring"],
        "times": ["Arranged"],
        "desc": "Capstone credit via approved data science internship.",
        "core_protected": False,
    },
    "DATA499": {
        "name": "Data Science Honors Thesis",
        "credits": 2, "type": "major", "prereqs": ["DATA229", "DATA327"],
        "offered": ["Fall", "Spring"],
        "times": ["Arranged"],
        "desc": "Independent research culminating in a faculty-supervised honors thesis.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # ACCOUNTING
    # ══════════════════════════════════════════════════════════════
    "ACCT225": {
        "name": "Financial Accounting",
        "credits": 4, "type": "major", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "TTH 11:00-12:15pm"],
        "desc": "Preparation and interpretation of financial statements (GAAP).",
        "core_protected": False,
    },
    "ACCT226": {
        "name": "Managerial Accounting",
        "credits": 4, "type": "major", "prereqs": ["ACCT225"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 9:30-10:45am"],
        "desc": "Cost accounting, budgeting, and internal decision-making.",
        "core_protected": False,
    },
    "ACCT325": {
        "name": "Intermediate Accounting",
        "credits": 4, "type": "elective", "prereqs": ["ACCT225"],
        "offered": ["Fall"],
        "times": ["MWF 10:00-10:50am"],
        "desc": "In-depth study of financial reporting standards and GAAP.",
        "core_protected": False,
    },
    "ACCT337": {
        "name": "Cost Accounting",
        "credits": 4, "type": "elective", "prereqs": ["ACCT226"],
        "offered": ["Spring"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Product costing, variance analysis, and managerial control.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # BUSINESS
    # ══════════════════════════════════════════════════════════════
    "BUSN210": {
        "name": "Business & Economic Statistics",
        "credits": 4, "type": "major", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["TTH 9:30-10:45am", "MWF 11:00-11:50am"],
        "desc": "Statistical methods applied to business and economic decision-making.",
        "core_protected": False,
    },
    "BUSN212": {
        "name": "Business Research Methods",
        "credits": 4, "type": "major", "prereqs": ["BUSN210"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 2:30-3:45pm"],
        "desc": "Research design, data collection, and analysis for business problems.",
        "core_protected": False,
    },
    "BUSN315": {
        "name": "Business Analytics",
        "credits": 4, "type": "elective", "prereqs": [],
        "offered": ["Spring"],
        "times": ["MWF 1:00-1:50pm"],
        "desc": "Spreadsheet modeling, data-driven decision-making, and dashboards. Recommended: BUSN210 or DATA227.",
        "core_protected": False,
    },
    "BUSN321": {
        "name": "Strategic Logistics & Operations Management",
        "credits": 4, "type": "elective", "prereqs": ["BUSN210"],
        "offered": ["Fall"],
        "times": ["MWF 1:00-1:50pm", "TTH 11:00-12:15pm"],
        "desc": "Supply chain design, logistics, and operations strategy.",
        "core_protected": False,
    },
    "BUSN328": {
        "name": "Introduction to Project Management",
        "credits": 4, "type": "elective", "prereqs": [],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am"],
        "desc": "Project lifecycle, scheduling, risk management, and Agile methods.",
        "core_protected": False,
    },
    "BUSN330": {
        "name": "Financial Management",
        "credits": 4, "type": "major", "prereqs": ["ACCT225", "ECON200"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 11:00-11:50am", "TTH 9:30-10:45am"],
        "desc": "Corporate finance, capital budgeting, NPV, WACC, and capital structure.",
        "core_protected": False,
    },
    "BUSN340": {
        "name": "Marketing Management",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall", "Spring"],
        "times": ["TTH 11:00-12:15pm", "MWF 2:00-2:50pm"],
        "desc": "Marketing strategy, consumer behavior, and the marketing mix.",
        "core_protected": False,
    },
    "BUSN355": {
        "name": "Student Managed Investment Fund",
        "credits": 4, "type": "elective", "prereqs": ["BUSN330"],
        "offered": ["Spring"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Hands-on equity research and portfolio management using real funds.",
        "core_protected": False,
    },
    "BUSN365": {
        "name": "Managing Effective Organizations",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 1:00-2:15pm"],
        "desc": "Organizational behavior, leadership, and human resource management.",
        "core_protected": False,
    },
    "BUSN381": {
        "name": "Business Internship",
        "credits": 4, "type": "major", "prereqs": ["BUSN330"],
        "offered": ["Fall", "Spring"],
        "times": ["Arranged"],
        "desc": "Professional work experience with an approved employer (0-4 credits).",
        "core_protected": False,
    },
    "BUSN430": {
        "name": "Investment Analysis",
        "credits": 4, "type": "major", "prereqs": ["BUSN330"],
        "offered": ["Spring"],
        "times": ["MWF 2:00-2:50pm"],
        "desc": "Security valuation, portfolio theory, derivatives, and risk.",
        "core_protected": False,
    },
    "BUSN460": {
        "name": "Strategic Planning & Policy",
        "credits": 4, "type": "elective", "prereqs": ["BUSN330"],
        "offered": ["Spring"],
        "times": ["TTH 2:30-3:45pm"],
        "desc": "Corporate strategy, competitive analysis, and business policy.",
        "core_protected": False,
    },
    "BUSN442": {
        "name": "Creative Promotion Strategy",
        "credits": 4, "type": "elective", "prereqs": ["BUSN340"],
        "offered": ["Fall"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Advertising, brand management, and integrated marketing communications.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # ECONOMICS
    # ══════════════════════════════════════════════════════════════
    "ECON200": {
        "name": "Principles of Economics",
        "credits": 4, "type": "major", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 9:00-9:50am", "TTH 9:30-10:45am", "TTH 1:00-2:15pm"],
        "desc": "Micro and macro foundations: supply, demand, markets, and policy.",
        "core_protected": False,
    },
    "ECON225": {
        "name": "Money and Banking",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall"],
        "times": ["TTH 11:00-12:15pm"],
        "desc": "Banking systems, monetary policy, and financial markets.",
        "core_protected": False,
    },
    "ECON280": {
        "name": "Managerial Economics",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall"],
        "times": ["MWF 10:00-10:50am"],
        "desc": "Economic theory applied to managerial decisions and firm behavior.",
        "core_protected": False,
    },
    "ECON300": {
        "name": "Econometrics",
        "credits": 4, "type": "major", "prereqs": ["ECON200"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 11:00-11:50am", "TTH 2:30-3:45pm"],
        "desc": "Regression analysis and statistical inference for economic data. Requires ECON200 + intro stats (BUSN210 or DATA227).",
        "core_protected": False,
        "prereqs_any": ["DATA227", "BUSN210"],  # student needs ONE of these + ECON200
    },
    "ECON310": {
        "name": "Intermediate Microeconomic Theory",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am"],
        "desc": "Advanced price theory, consumer optimization, and market structure.",
        "core_protected": False,
    },
    "ECON311": {
        "name": "Intermediate Macroeconomic Theory",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Spring"],
        "times": ["MWF 11:00-11:50am"],
        "desc": "National income, inflation, unemployment, and growth models.",
        "core_protected": False,
    },
    "ECON312": {
        "name": "Fundamentals of Forecasting",
        "credits": 4, "type": "elective", "prereqs": ["ECON300"],
        "offered": ["Spring"],
        "times": ["MWF 2:00-2:50pm"],
        "desc": "Time series analysis, forecasting methods, and econometric modeling.",
        "core_protected": False,
    },
    "ECON315": {
        "name": "Labor Economics",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Spring"],
        "times": ["TTH 1:00-2:15pm"],
        "desc": "Labor markets, wages, human capital, and employment policy.",
        "core_protected": False,
    },
    "ECON330": {
        "name": "International Trade & Finance",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Spring"],
        "times": ["TTH 1:00-2:15pm"],
        "desc": "Trade theory, exchange rates, balance of payments, and global capital.",
        "core_protected": False,
    },
    "ECON340": {
        "name": "Public Finance",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall"],
        "times": ["MWF 1:00-1:50pm"],
        "desc": "Government spending, taxation, fiscal policy, and public goods.",
        "core_protected": False,
    },
    "ECON360": {
        "name": "Industrial Organization",
        "credits": 4, "type": "elective", "prereqs": ["ECON200"],
        "offered": ["Fall"],
        "times": ["TTH 9:30-10:45am"],
        "desc": "Market power, oligopoly, antitrust, and regulation.",
        "core_protected": False,
    },
    "ECON400": {
        "name": "Senior Seminar in Economics",
        "credits": 4, "type": "major", "prereqs": ["ECON300", "BUSN330"],
        "offered": ["Spring"],
        "times": ["TTH 2:30-3:45pm"],
        "desc": "Senior capstone integrating economics, finance, and independent research.",
        "core_protected": True,
    },

    # ══════════════════════════════════════════════════════════════
    # ENVIRONMENTAL SCIENCE (DS electives)
    # ══════════════════════════════════════════════════════════════
    "ESCI290": {
        "name": "Environmental Data Analysis",
        "credits": 4, "type": "elective", "prereqs": ["DATA227"],
        "offered": ["Spring"],
        "times": ["TTH 1:00-2:15pm"],
        "desc": "Statistical and computational methods for environmental datasets.",
        "core_protected": False,
    },
    "ESCI291": {
        "name": "Environmental Data Applications",
        "credits": 4, "type": "elective", "prereqs": ["ESCI290"],
        "offered": ["Fall"],
        "times": ["TTH 1:00-2:15pm"],
        "desc": "Applied environmental data science with GIS and remote sensing.",
        "core_protected": False,
    },

    # ══════════════════════════════════════════════════════════════
    # PSYCHOLOGY (DS electives)
    # ══════════════════════════════════════════════════════════════
    "PSYC201": {
        "name": "Statistics in Psychology (Intro Stats equiv.)",
        "credits": 4, "type": "elective", "prereqs": [],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 10:00-10:50am", "TTH 11:00-12:15pm"],
        "desc": "Statistical methods as applied to psychological research.",
        "core_protected": False,
    },
    "PSYC202": {
        "name": "Research Methods in Psychology",
        "credits": 4, "type": "elective", "prereqs": ["PSYC201"],
        "offered": ["Fall", "Spring"],
        "times": ["MWF 1:00-1:50pm"],
        "desc": "Experimental design, data analysis, and scientific writing.",
        "core_protected": False,
    },
}


# ══════════════════════════════════════════════════════════════════
# DEGREE REQUIREMENTS — 2025-26 Catalog
# Total credits: 126 (per wittenberg.edu/administration/registrar/general-academic-information)
# Connections Curriculum: ~36 credits (8 courses × 4 credits + FY seminar)
# ══════════════════════════════════════════════════════════════════

MAJOR_REQUIREMENTS = {

    # ── DATA SCIENCE ─────────────────────────────────────────────────────────
    # Source: 2025-26 Catalog p.79 + wittenberg.edu/academics/data-science
    # 43 credits in major: 27 required + 16 electives
    # ─────────────────────────────────────────────────────────────────────────
    "data_science": {
        "name": "Data Science (B.A.)",
        "major_credits": 43,
        "connections_credits": 32,
        "total_credits": 126,

        # Connections Curriculum (gen ed)
        "core_connections": [
            "WITT101", "ENGL101", "HIST101", "ARTS101",
            "LANG101", "LANG102", "SCI101", "RELI101",
        ],

        # Required — 27 credits
        "major_required": [
            "DATA229",  # Intro to Data Science (prereq: DATA227)
            "DATA327",  # Statistical Modeling (prereq: DATA227)
            "COMP150",  # Computer Programming I
            "COMP290",  # Database Systems (prereq: COMP150)
            "DATA490",  # Capstone — 2 credits (or DATA491/DATA499)
        ],

        # OR groups — student picks ONE from each
        "major_choice_groups": [
            {
                "label": "Introductory Statistics",
                "choose": 1,
                "options": ["DATA227", "BUSN210", "PSYC201"],
                "note": "Required intro stats — pick the one that best fits your background",
            },
            {
                "label": "Calculus Experience",
                "choose": 1,
                "options": ["MATH131", "MATH201"],
                "note": "MATH201 recommended if considering graduate study",
            },
        ],

        # Electives — 16 credits (4 courses × 4cr)
        "major_electives": {
            "count": 4,
            "options": [
                "BUSN315", "COMP250", "COMP265", "COMP275", "COMP340",
                "COMP350", "COMP353", "DATA280", "DATA337", "DATA380",
                "ECON300", "ESCI290", "ESCI291", "MATH228", "MATH261",
                "MATH328", "PSYC202",
            ],
        },

        "constraints": [
            "COMP150 before all COMP 200+ courses",
            "DATA227 (or equiv) before DATA229 and DATA327",
            "DATA229 before DATA337, DATA380, DATA490",
            "DATA327 before DATA380",
            "COMP250 before COMP340, COMP350, COMP353",
            "DATA490 capstone in final year only",
            "Max 18 credits/semester",
            "126 total credits to graduate",
        ],
    },

    # ── FINANCE ──────────────────────────────────────────────────────────────
    # Source: 2025-26 Catalog p.68 + wittenberg.edu/academics/finance
    # 52 credits: 36 required in Business/Econ + 4 related dept + 12 electives
    # ─────────────────────────────────────────────────────────────────────────
    "finance": {
        "name": "Finance (B.A.)",
        "major_credits": 52,
        "connections_credits": 32,
        "total_credits": 126,

        "core_connections": [
            "WITT101", "ENGL101", "HIST101", "ARTS101",
            "LANG101", "LANG102", "SCI101", "RELI101",
        ],

        # Required in Business & Economics — 36 credits
        # BUSN 381 internship is 0-4 credits; modeled as 4 here for planning
        "major_required": [
            "ACCT225",  # Financial Accounting
            "ECON200",  # Principles of Economics
            "BUSN210",  # Business & Economic Statistics
            "ECON300",  # Econometrics (prereqs: ECON200, DATA227)
            "BUSN330",  # Financial Management (prereqs: ACCT225, ECON200)
            "BUSN430",  # Investment Analysis (prereq: BUSN330)
            "ECON400",  # Senior Seminar (prereqs: ECON300, BUSN330) — capstone
            "BUSN381",  # Business Internship (prereq: BUSN330)
        ],

        # OR groups — student picks ONE from each
        "major_choice_groups": [
            {
                "label": "Intermediate Economics",
                "choose": 1,
                "options": ["ECON310", "ECON280"],
                "note": "ECON 310 Intermediate Microeconomics OR ECON 280 Managerial Econ",
            },
            {
                "label": "Quantitative Requirement (Related Dept)",
                "choose": 1,
                "options": ["DATA327", "MATH131", "MATH201"],
                "note": "DATA 327 Statistical Modeling OR MATH 131 OR MATH 201",
            },
        ],

        # Finance Electives — 12 credits
        # Per catalog: 2 courses from specified list + 1 free ACCT/BUSN/ECON
        # Modeled as "choose 3 from expanded pool"
        "major_electives": {
            "count": 3,
            "options": [
                "ACCT325", "BUSN355", "ECON225", "ECON312",
                "ECON330", "ECON340",
                # Free elective from any ACCT/BUSN/ECON — using additional options:
                "ECON280", "ECON310", "ECON315", "ECON360",
                "BUSN315", "BUSN212", "ACCT226", "ACCT337",
            ],
        },

        "constraints": [
            "ACCT225 before BUSN330",
            "ECON200 before BUSN330 and ECON300",
            "DATA227 (or BUSN210) before ECON300",
            "BUSN330 before BUSN430, BUSN381",
            "ECON300 + BUSN330 before ECON400 (Senior Seminar)",
            "ECON400 and BUSN381 in final year only",
            "Max 18 credits/semester",
            "126 total credits to graduate",
        ],
    },
}


# ══════════════════════════════════════════════════════════════════
# MOCK STUDENT PROFILES — updated with new course codes
# ══════════════════════════════════════════════════════════════════

MOCK_STUDENTS = [
    {
        "student_id": "WU-2026-001",
        "student_name": "Alex Rivera",
        "major": "data_science",
        "classification": "freshman",
        "completed_courses": [],
        "max_credits": 16,
        "prefers_morning": True,
        "prefers_light_fridays": False,
        "is_athlete": False,
        "is_full_time": True,
        "is_part_time": False,
    },
    {
        "student_id": "WU-2026-002",
        "student_name": "Jordan Lee",
        "major": "finance",
        "classification": "sophomore",
        "completed_courses": [
            "WITT101", "ENGL101", "MATH131", "ECON200",
            "ACCT225", "LANG101", "HIST101", "BUSN210",
        ],
        "max_credits": 16,
        "prefers_morning": False,
        "prefers_light_fridays": True,
        "is_athlete": True,
        "is_full_time": True,
        "is_part_time": False,
    },
    {
        "student_id": "WU-2026-003",
        "student_name": "Morgan Chen",
        "major": "data_science",
        "classification": "junior",
        "completed_courses": [
            "WITT101", "ENGL101", "MATH201", "MATH202",
            "COMP150", "COMP250", "DATA227", "DATA229",
            "DATA327", "LANG101", "LANG102", "HIST101",
            "SCI101", "ARTS101",
        ],
        "max_credits": 18,
        "prefers_morning": False,
        "prefers_light_fridays": False,
        "is_athlete": False,
        "is_full_time": True,
        "is_part_time": False,
    },
    {
        "student_id": "WU-2026-004",
        "student_name": "Taylor Brooks",
        "major": "finance",
        "classification": "junior",
        "completed_courses": [
            "WITT101", "ENGL101", "MATH131", "ACCT225",
            "ECON200", "DATA227", "ECON300", "BUSN330",
            "HIST101", "LANG101", "LANG102", "SCI101",
            "ARTS101", "RELI101", "BUSN210",
        ],
        "max_credits": 14,
        "prefers_morning": True,
        "prefers_light_fridays": True,
        "is_athlete": False,
        "is_full_time": True,
        "is_part_time": False,
    },
    {
        "student_id": "WU-2026-005",
        "student_name": "Sam Patel",
        "major": "data_science",
        "classification": "sophomore",
        "completed_courses": [
            "WITT101", "ENGL101", "MATH131", "COMP150", "DATA227",
        ],
        "max_credits": 13,
        "prefers_morning": False,
        "prefers_light_fridays": False,
        "is_athlete": True,
        "is_full_time": True,
        "is_part_time": False,
    },
]
