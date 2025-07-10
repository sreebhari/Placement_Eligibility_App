import streamlit as st
import pandas as pd
import time
import pymysql

st.set_page_config(page_title="Placement Eligibility App", layout="wide")

progress=st.progress(0)
for i in range(100):
    time.sleep(0.1)
    progress.progress(i+1)
    
st.title("🎓 Placement Eligibility Filter")
st.markdown("Filter students based on placement readiness criteria.")


def get_connection():
    return pymysql.connect(
        host = '127.0.0.1',
        user='root',
        passwd='Imaiya14@',
        database = "placement_eligibiliy_db", 
        autocommit=True
    )

#connect to sql
myconnection=get_connection()

st.sidebar.title("Section")
sb=st.sidebar.selectbox('',['Filter','Insights'])


if sb=='Filter':
    st.sidebar.header("Eligibility Criteria")

    batch_filter = st.sidebar.selectbox("Batch", options=["All", "Batch A", "Batch B", "Batch C"])
    
    # Problem Solved
    df_min_max_ps=pd.read_sql_query("""select min(problems_solved) as min_ps,max(problems_solved) as max_ps from programming""",myconnection)
    min_ps = df_min_max_ps['min_ps'].iloc[0]
    max_ps = df_min_max_ps['max_ps'].iloc[0]

    min_problems = st.sidebar.number_input("Problems Solved (Min)", min_value=min_ps, max_value=max_ps, value=50)
    
    #Mock interview score
    df_min_max_mock=pd.read_sql_query("""select min(mock_interview_score) as min_mock, max(mock_interview_score) as max_mock from placements""",myconnection)
    min_mock = df_min_max_mock['min_mock'].iloc[0]
    max_mock = df_min_max_mock['max_mock'].iloc[0]
    
    min_mock_score = st.sidebar.number_input("Mock Interview Score (Min)", min_value=min_mock, max_value=max_mock, value=75)
    min_soft_skills = st.sidebar.number_input("Avg Soft Skills Score (Min)", min_value=0, max_value=100, value=75)
    status_filter = st.sidebar.selectbox("Placement Status", options=["All", "Ready", "Placed", "Not Ready"])
    

    
    def fetch_eligible_students():
        query = f"""
            SELECT 
                s.student_id
                , s.name
                , s.course_batch
                , p.problems_solved
                , ss.communication
                , ss.teamwork
                , ss.presentation
                , ss.leadership
                , ss.critical_thinking
                , ss.interpersonal_skills
                , pl.mock_interview_score
                , pl.placement_status
                , pl.company_name
            FROM students s
            JOIN programming p ON s.student_id = p.student_id
            JOIN soft_skills ss ON s.student_id = ss.student_id
            JOIN placements pl ON s.student_id = pl.student_id
            WHERE 
                p.problems_solved >= {min_problems} AND
                ( (ss.communication + ss.teamwork + ss.presentation + ss.leadership + ss.critical_thinking + ss.interpersonal_skills)/6.0 ) >= {min_soft_skills} AND
                pl.mock_interview_score >= {min_mock_score}
        """
    
        if status_filter != "All":
            query += f" AND pl.placement_status = '{status_filter}'"
        
        if batch_filter != "All":
            query += f" AND s.course_batch = '{batch_filter}'"
    
        with myconnection:
            df = pd.read_sql(query, myconnection)
        return df
        
    if st.button("🔎 Show Eligible Students"):
        result_df = fetch_eligible_students()

        if result_df.empty:
            st.warning("No students match the criteria.")
        else:
            st.success(f"{len(result_df)} students found!")
            st.dataframe(result_df)

if sb=='Insights':
    st.subheader("📊 Placement Insights & Analytics")
    v2=st.selectbox('Select Scenario',['1. total number of students in each bach',
                                       '2. Top 5 Students Ready for Placement (Highest Mock Score)',
                                       '3. Average Programming Performance Per Batch',
                                       '4. Distribution of Soft Skills Scores (Average per Student)',
                                       '5. placement percentage across each batch',
                                       '6. Placement Readiness vs Actual Placement',
                                       '7. Students with Highest Number of Certifications',
                                       '8. Average Placement Package by City',
                                       '9. top 10 Student with higest package',
                                       '10. Students with Highest Overall Score',
                                      ],index=0)
    
    if v2=='1. total number of students in each bach':
        df=pd.read_sql_query("""
            select 
                course_batch
                ,count(*) as total_students 
            from students group by 1 order by 1""",myconnection)
        st.table(df)
        
    if v2=='2. Top 5 Students Ready for Placement (Highest Mock Score)':
        df=pd.read_sql_query("""
            SELECT 
                s.name
                , pl.mock_interview_score
                , p.problems_solved
            FROM students s
            JOIN placements pl ON s.student_id = pl.student_id
            JOIN programming p ON s.student_id = p.student_id
            JOIN soft_skills ss ON s.student_id = ss.student_id
            WHERE pl.placement_status = 'Ready'
            ORDER BY pl.mock_interview_score DESC
            LIMIT 5""",myconnection)
        st.table(df)
        
    if v2=='3. Average Programming Performance Per Batch':
        df=pd.read_sql_query("""
            SELECT 
                s.course_batch
                ,p.language
                , round(AVG(p.problems_solved),2) AS avg_problems
            FROM students s
            JOIN programming p ON s.student_id = p.student_id
            GROUP BY 1,2
            ORDER BY 1,3 desc""",myconnection)
        st.table(df)
        
    if v2=='4. Distribution of Soft Skills Scores (Average per Student)':
        df=pd.read_sql_query("""
            SELECT 
                s.name,
                ROUND((ss.communication + ss.teamwork + ss.presentation + ss.leadership + ss.critical_thinking + ss.interpersonal_skills)/6, 2) AS avg_soft_skills
            FROM students s
            JOIN soft_skills ss ON s.student_id = ss.student_id
            ORDER BY avg_soft_skills DESC""",myconnection)
        st.table(df)
    
    if v2=='5. placement percentage across each batch':
        df=pd.read_sql_query("""
            SELECT 
                s.course_batch,
                COUNT(*) AS total_students,
                ROUND(
                    (COUNT(CASE WHEN p.placement_status = 'Placed' THEN 1 END) / COUNT(*)) * 100, 0
                ) AS placed_percentage
                ,ROUND(
                    (COUNT(CASE WHEN p.placement_status = 'Ready' THEN 1 END) / COUNT(*)) * 100, 0
                ) AS ready_percentage
                ,ROUND(
                    (COUNT(CASE WHEN p.placement_status = 'Not Ready' THEN 1 END) / COUNT(*)) * 100, 0
                ) AS not_ready_percentage
            FROM students s
            JOIN placements p ON s.student_id = p.student_id
            GROUP BY 1
            ORDER BY 1""",myconnection)
        st.table(df)
    
    if v2=='6. Placement Readiness vs Actual Placement':
        df=pd.read_sql_query("""
            SELECT 
                placement_status
                , COUNT(*) AS count
            FROM placements
            WHERE placement_status IN ('Ready', 'Placed')
            GROUP BY placement_status""",myconnection)
        st.table(df)

    if v2=='7. Students with Highest Number of Certifications':
        df=pd.read_sql_query("""
            SELECT 
                s.name
                , p.certifications_earned
            FROM students s
            JOIN programming p ON s.student_id = p.student_id
            ORDER BY p.certifications_earned DESC""",myconnection)
        st.table(df)

    if v2=='8. Average Placement Package by City':
        df=pd.read_sql_query("""
            SELECT 
                s.city
                , AVG(pl.placement_package) AS avg_package
            FROM students s
            JOIN placements pl ON s.student_id = pl.student_id
            WHERE pl.placement_status = 'Placed'
            GROUP BY s.city
            ORDER BY avg_package DESC""",myconnection)
        st.table(df)

    if v2=='9. top 10 Student with higest package':
        df=pd.read_sql_query("""
            SELECT 
                s.name
                , pl.placement_package
            FROM students s
            JOIN placements pl ON s.student_id = pl.student_id
            WHERE pl.placement_status = 'Placed'
            ORDER BY placement_package DESC
            limit 10""",myconnection)
        st.table(df)

    if v2=='10. Students with Highest Overall Score':
        df=pd.read_sql_query("""
            SELECT s.name,
                   p.problems_solved,
                   ROUND((ss.communication + ss.teamwork + ss.presentation + ss.leadership + ss.critical_thinking + ss.interpersonal_skills)/6, 2) AS avg_soft_skills,
                   (p.problems_solved + ((ss.communication + ss.teamwork + ss.presentation + ss.leadership + ss.critical_thinking + ss.interpersonal_skills)/6)) AS total_score
            FROM students s
            JOIN programming p ON s.student_id = p.student_id
            JOIN soft_skills ss ON s.student_id = ss.student_id
            ORDER BY total_score DESC
            LIMIT 5""",myconnection)
        st.table(df)

        
    def avg_problems_per_batch():
        query = """
            SELECT s.course_batch, AVG(p.problems_solved) AS avg_problems
            FROM students s
            JOIN programming p ON s.student_id = p.student_id
            GROUP BY s.course_batch
            ORDER BY avg_problems DESC
        """
        conn = get_connection()
        with conn:
            df = pd.read_sql(query, conn)
        return df
    
    with st.expander("📌 Avg Problems Solved per Batch"):
        df1 = avg_problems_per_batch()
        st.bar_chart(df1.set_index("course_batch"))
        
        
    def top_students_ready():
        query = """
            SELECT s.name, pl.mock_interview_score, p.problems_solved,
                   (ss.communication + ss.teamwork + ss.presentation + ss.leadership + ss.critical_thinking + ss.interpersonal_skills)/6 AS avg_soft_skills
            FROM students s
            JOIN placements pl ON s.student_id = pl.student_id
            JOIN programming p ON s.student_id = p.student_id
            JOIN soft_skills ss ON s.student_id = ss.student_id
            WHERE pl.placement_status = 'Ready'
            ORDER BY mock_interview_score DESC, avg_soft_skills DESC
            LIMIT 5
        """
        conn = get_connection()
        with conn:
            df = pd.read_sql(query, conn)
        return df
    
    with st.expander("🏆 Top 5 Students Ready for Placement"):
        df2 = top_students_ready()
        st.table(df2)
       
    
    def placement_distribution():
        query = """
            SELECT placement_status, COUNT(*) AS count
            FROM placements
            GROUP BY placement_status
        """
        conn = get_connection()
        with conn:
            df = pd.read_sql(query, conn)
        return df
    
    with st.expander("📈 Placement Status Distribution"):
        df3 = placement_distribution()
        st.dataframe(df3)
        st.bar_chart(df3.set_index("placement_status"))
        
    def top_cities_by_placements():
        query = """
            SELECT s.city, COUNT(*) AS placed_count
            FROM students s
            JOIN placements pl ON s.student_id = pl.student_id
            WHERE pl.placement_status = 'Placed'
            GROUP BY s.city
            ORDER BY placed_count DESC
            LIMIT 5
        """
        conn = get_connection()
        with conn:
            df = pd.read_sql(query, conn)
        return df
    
    with st.expander("🌆 Top 5 Cities by Placed Students"):
        df4 = top_cities_by_placements()
        st.bar_chart(df4.set_index("city"))