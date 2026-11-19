"""The resume, in the plain form the resume page shows. Wording follows the PDF."""

from config.Position import Position


class Resume:
    """Experience, education, certifications and skills from the resume PDF."""

    SUMMARY = (
        "Applied AI scientist with 9+ years of experience designing and deploying machine learning systems that "
        "quantify customer value, forecast demand and optimize pricing. Owns the model lifecycle from feature "
        "engineering, experimentation and backtesting through deployment, monitoring and governance."
    )

    EXPERIENCE = (
        Position(
            "Lead Applied AI Scientist",
            "Signature Aviation",
            "Orlando, FL",
            "Jul 2026 to Present",
            (
                "Built and lead Signature Aviation's enterprise AI platform, a shared codebase that standardizes how "
                "data scientists develop, experiment with and register models to Unity Catalog.",
                "Architected a multi model forecasting platform with Chronos-2, Greykite and baseline autoregressive "
                "models behind a shared interface.",
                "Established a governed MLOps lifecycle in MLflow and Unity Catalog with rolling origin backtesting, "
                "Optuna tuning and automated selection of the most accurate approved model.",
            ),
        ),
        Position(
            "Senior Data Scientist",
            "Signature Aviation",
            "Orlando, FL",
            "May 2022 to Jul 2026",
            (
                "Developed the dynamic pricing system for hourly parking, which turns ramp demand forecasts at each "
                "FBO into demand based price multipliers.",
                "Built a customer behavior simulation and pricing optimization platform across fuel, ground power "
                "and hourly parking.",
                "Led the analytical evaluation of a major acquisition with an independent model of flight growth, "
                "net revenue and risk.",
            ),
        ),
        Position(
            "Senior Data Scientist II",
            "GHD",
            "Buffalo, NY",
            "Jul 2020 to May 2022",
            (
                "Led design, development and deployment of machine learning software that automates and optimizes "
                "pipeline operations across major North American oil and gas networks.",
            ),
        ),
        Position("Data Scientist", "GHD", "Buffalo, NY", "Aug 2018 to Jun 2019"),
        Position(
            "Data Scientist",
            "VyStar Credit Union",
            "Jacksonville, FL",
            "Jun 2019 to Jul 2020",
            (
                "Delivered a marketing propensity model (LightGBM in Databricks) for CD and credit card campaigns "
                "that raised member response rates about 10x.",
            ),
        ),
    )

    EARLIER_EXPERIENCE = (
        Position(
            "Founder and Data Scientist (part time)", "Golden Oak Research", "Rochester, NY", "Aug 2017 to Jan 2020"
        ),
        Position("Data Scientist Intern", "Soleo", "Rochester, NY", "Mar 2018 to Jul 2018"),
        Position("Data Scientist Intern", "Howe & Rusling, Inc.", "Rochester, NY", "May 2016 to Aug 2016"),
    )

    EDUCATION = (
        ("Syracuse University", "Master of Science in Applied Data Science", "2019 to 2022"),
        ("Rochester Institute of Technology", "Bachelor of Science in Data Science", "2018"),
    )

    CERTIFICATIONS = (
        ("Databricks Certified Context Engineer Associate", "Issued Jul 2026"),
        ("MIT Professional Education, Applied AI and Data Science Program", "Completed Jun 2026"),
    )

    ACHIEVEMENTS = (
        (
            "NFL Big Data Bowl (Kaggle)",
            "Spring 2020",
            "Ranked 24th overall out of 2,000+ teams (11th among solo competitors) with a PyTorch CNN that predicts "
            "yards per carry.",
        ),
    )

    SKILLS = (
        ("Languages", "Python, PySpark, SQL, R, MATLAB"),
        (
            "ML and frameworks",
            "PyTorch, LightGBM, XGBoost, CatBoost, Keras, scikit-learn, Spark ML, Hugging Face, Greykite, Chronos-2",
        ),
        ("Cloud and tools", "Databricks, Azure, Delta Lake, MLflow, Unity Catalog, Power BI, Optuna, GitHub Actions"),
    )
