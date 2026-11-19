"""The full resume as shown on the resume page. Text matches the PDF word for word.

To update the site after the resume changes, edit the entries below in the
same order as the PDF and replace assets/files/Alexander_Geiger_Resume.pdf.
The phone number and personal email stay in the PDF only.
"""

from config.ResumeEmployer import ResumeEmployer
from config.ResumeItem import ResumeItem
from config.ResumeRole import ResumeRole


class Resume:
    """Header, summary, skills, experience, education, certifications and achievements, in resume order."""

    NAME = "ALEXANDER J. GEIGER"
    HEADLINE = "Lead Applied AI Scientist"
    LOCATION = "Orlando, FL"
    LINKS = (
        ("linkedin.com/in/ajgeiger", "https://www.linkedin.com/in/ajgeiger"),
        ("github.com/ajgeiger", "https://github.com/ajgeiger"),
        ("kaggle.com/alexgeiger", "https://www.kaggle.com/alexgeiger"),
        ("goldenoakresearch.com", "https://goldenoakresearch.com"),
    )

    SUMMARY_TITLE = "Professional Summary"
    SUMMARY = (
        "Applied AI scientist with 9+ years of experience designing and deploying machine learning systems that "
        "quantify customer value, forecast demand, and optimize pricing to maximize net revenue. Builds "
        "production MLOps frameworks in Databricks and MLflow for a global private aviation network and owns the "
        "model lifecycle from feature engineering, experimentation, and backtesting through deployment, "
        "monitoring, and governance. Works across commercial and technical teams to deliver dynamic pricing and "
        "forecasting across 100+ locations, protecting millions in margin."
    )

    SKILLS_TITLE = "Technical Skills"
    SKILLS = (
        ("Languages", "Python, PySpark, SQL, R, MATLAB"),
        (
            "ML & Frameworks",
            "PyTorch, LightGBM, XGBoost, CatBoost, Keras, scikit-learn, Spark ML, Hugging Face, Greykite, Chronos-2",
        ),
        ("Cloud & Tools", "Databricks, Azure, Delta Lake, MLflow, Unity Catalog, Power BI, Optuna, GitHub Actions"),
        (
            "Domain Expertise",
            (
                "Revenue Management & Dynamic Pricing, Demand Forecasting, Behavioral Modeling, Constraint "
                "Optimization, A/B Testing, Monte Carlo Simulation, Markov Models, NLP"
            ),
        ),
    )

    EXPERIENCE_TITLE = "Professional Experience"
    EXPERIENCE = (
        ResumeEmployer(
            name="Signature Aviation",
            location="Orlando, FL",
            dates="May 2022 to Present",
            roles=(
                ResumeRole(
                    title="Lead Applied AI Scientist",
                    dates="Jul 2026 to Present",
                    note=(
                        "Report to the SVP of Advanced Analytics. Thousands of models in production across 100+ "
                        "locations."
                    ),
                    bullets=(
                        (
                            "Built and lead Signature Aviation's enterprise AI platform, a shared codebase and "
                            "common repository that standardizes how data scientists across the organization "
                            "develop, experiment with, and register models to Unity Catalog. It supports "
                            "forecasting, behavioral modeling, NLP analysis, dynamic pricing, and MLOps "
                            "governance from raw operational data through to production."
                        ),
                        (
                            "Architected a multi-model forecasting platform with Chronos-2 (time-series "
                            "foundation model), Greykite, and baseline autoregressive models behind a shared "
                            "interface, including hybrid models that pair Greykite's holiday and event impact "
                            "estimates with Chronos-2 forecasts."
                        ),
                        (
                            "Established a governed MLOps lifecycle (Testing, Challenger, Champion, Retired) "
                            "with models registered in Unity Catalog and all experimentation in MLflow, using "
                            "rolling-origin backtesting, Optuna tuning with warm-start search spaces, and "
                            "automated feature selection. Production forecasts select the most accurate approved "
                            "model for each base and horizon from a scoreboard of WAPE, MAPE, MAE, RMSE, and "
                            "bias. Reviewed 2,000+ tracked experiment runs and redirected effort away from "
                            "low-impact settings."
                        ),
                        (
                            "Put reliability and observability into production. Automated health checks "
                            "(PASS/WARN/FAIL) flag stale, missing, or duplicated data, job runs are monitored "
                            "through Databricks system tables, and CI/CD unit testing runs through GitHub "
                            "Actions."
                        ),
                    ),
                ),
                ResumeRole(
                    title="Senior Data Scientist",
                    dates="May 2022 to Jul 2026",
                    bullets=(
                        (
                            "Developed the dynamic pricing system for hourly parking, which forecasts ramp "
                            "demand at each FBO (fixed base operator) and converts those forecasts into "
                            "demand-based price multipliers that stay constant for the day, with accuracy "
                            "tracking for business users. Built a Customer Behavior Simulation and Pricing "
                            "Optimization platform that models price sensitivity from historical purchases "
                            "across fuel, ground power (GPU), and hourly parking, combining propensity modeling, "
                            "expected-value simulation, and optimization to find segment-level pricing that "
                            "maximizes net revenue while quantifying downside risk before deployment."
                        ),
                        (
                            "Designed and built a hangar capacity optimization and resident targeting engine "
                            "that quantified standalone market value plus incremental network revenue from "
                            "residency, supporting retain, replace, or vacate decisions and prioritizing the "
                            "highest-value prospective residents under capacity constraints."
                        ),
                        (
                            "Led the analytical evaluation of a major acquisition with an independent model "
                            "forecasting base-level flight growth, net revenue, and risk, using seasonal "
                            "patterns, growth assumptions, pricing scenarios, and capture risk to challenge "
                            "aggressive projections."
                        ),
                        (
                            "Implemented a risk-adjusted cost-plus pricing framework during a deicing supply "
                            "crisis, run as an automated Databricks pricing algorithm with automated "
                            "notifications, protecting millions in margin."
                        ),
                        (
                            "Built a fraud analytics framework to detect TailWins loyalty program accrual "
                            "patterns inconsistent with legitimate customer behavior after concerns about "
                            "employee ID misuse, prioritizing suspicious accounts for investigation. Built a "
                            "topic model (sentence-transformer embeddings with BERTopic) to find root-cause "
                            "themes in credit invoice comments and a fuel-purchase propensity model "
                            "(cross-validated LightGBM), and analyzed debit, credit, and rebill patterns to "
                            "support revenue integrity."
                        ),
                    ),
                ),
            ),
        ),
        ResumeEmployer(
            name="GHD",
            location="Buffalo, NY",
            roles=(
                ResumeRole(
                    title="Senior Data Scientist II",
                    dates="Jul 2020 to May 2022",
                    bullets=(
                        (
                            "Led design, development, and deployment of machine learning software that automates "
                            "and optimizes pipeline operations across major North American oil & gas networks, "
                            "supporting three operating strategies: Efficiency, Scheduled Delivery, and "
                            "High-Throughput."
                        ),
                        (
                            "Engineered an automated control system with SCADA integration (or operator-advisory "
                            "mode) to manage drag reducing agent (DRA) injection, pump activation, and target "
                            "flow-rate optimization."
                        ),
                        (
                            "Designed and implemented technology to mitigate pipeline pressure spikes by "
                            "modeling transient wave propagation using Fourier transforms and deploying "
                            "automated countermeasures that induced destructive interference, reducing stress "
                            "and improving reliability."
                        ),
                        (
                            "Owned the full lifecycle from architecture through production monitoring, enabling "
                            "real-time decision support for pipeline controllers and improving operational "
                            "control."
                        ),
                    ),
                ),
                ResumeRole(
                    title="Data Scientist",
                    dates="Aug 2018 to Jun 2019",
                    bullets=(),
                ),
            ),
        ),
        ResumeEmployer(
            name="VyStar Credit Union",
            location="Jacksonville, FL",
            roles=(
                ResumeRole(
                    title="Data Scientist",
                    dates="Jun 2019 to Jul 2020",
                    bullets=(
                        (
                            "Delivered a marketing propensity model (LightGBM in Databricks) for CD and credit "
                            "card campaigns that raised member response rates about 10x (over 950% improvement)."
                        ),
                        (
                            "Built credit card engagement models to identify high-propensity members for new "
                            "category-bonus rewards and developed member attrition prediction models using Azure "
                            "and PySpark."
                        ),
                        (
                            "Deployed demand forecasting models in Databricks and built Power BI dashboards to "
                            "track KPIs and model lift."
                        ),
                    ),
                ),
            ),
        ),
        ResumeEmployer(
            name="Earlier Experience",
            roles=(
                ResumeRole(
                    organization="Golden Oak Research",
                    title="Founder & Data Scientist (part-time)",
                    location="Rochester, NY",
                    dates="Aug 2017 to Jan 2020",
                    bullets=(
                        (
                            "Founded an LLC to source, parse, and monetize hard-to-find public datasets; built "
                            "an interactive analytics website (HTML5/JavaScript/Python/AWS) and developed a "
                            "Markov Decision Process simulation in JavaScript."
                        ),
                    ),
                ),
                ResumeRole(
                    organization="Soleo",
                    title="Data Scientist Intern",
                    location="Rochester, NY",
                    dates="Mar 2018 to Jul 2018",
                    bullets=(
                        (
                            "Analyzed regional business density and routed-call performance using Python, "
                            "Hadoop/Hive, and SQL to identify underserved markets and optimize routing paths and "
                            "partner mixes."
                        ),
                    ),
                ),
                ResumeRole(
                    organization="Howe & Rusling, Inc.",
                    title="Data Scientist Intern",
                    location="Rochester, NY",
                    dates="May 2016 to Aug 2016",
                    bullets=(
                        (
                            "Forecasted monetary policy impacts on factor markets; built Python data pipelines "
                            "interfacing with Bloomberg APIs and performed statistical factor model analysis on "
                            "Vanguard portfolios."
                        ),
                    ),
                ),
            ),
        ),
    )

    EDUCATION_TITLE = "Education"
    EDUCATION = (
        ResumeItem(
            title="Syracuse University",
            detail="Master of Science in Applied Data Science",
            dates="2019 to 2022",
        ),
        ResumeItem(
            title="Rochester Institute of Technology",
            detail="Bachelor of Science in Data Science",
            dates="2018",
        ),
    )

    CERTIFICATIONS_TITLE = "Certifications"
    CERTIFICATIONS = (
        ResumeItem(
            title="Databricks Certified Context Engineer Associate",
            dates="Issued Jul 2026, expires Jul 2028",
        ),
        ResumeItem(
            title="MIT Professional Education",
            detail="Applied AI and Data Science Program",
            dates="Completed Jun 2026",
        ),
    )

    ACHIEVEMENTS_TITLE = "Competitions & Achievements"
    ACHIEVEMENTS = (
        ResumeItem(
            title="NFL Big Data Bowl (Kaggle)",
            dates="Spring 2020",
            bullets=(
                (
                    "Ranked 24th overall out of 2,000+ teams (11th among solo competitors); developed a CNN "
                    "model using PyTorch to predict yards per carry while working full-time and completing "
                    "master's coursework."
                ),
            ),
        ),
    )
