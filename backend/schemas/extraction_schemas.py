from pydantic import BaseModel, Field

class AadhaarSchema(BaseModel):
    number: str | None = Field(description="Aadhaar card number")
    gender: str | None = Field(description="Male, Female, or Others")

class JeeEamcetSchema(BaseModel):
    ht_number: str | None = Field(description="Hall ticket number")
    rank: int | None = Field(description="Rank obtained")

class TCSchema(BaseModel):
    nationality: str | None = Field(description="Nationality of the student")
    religion: str | None = Field(description="Religion of the student")
    college_name: str | None = Field(description="Name of the college")
    caste: str | None = Field(description="Caste category as per the TC")

class SubjectScoresSchema(BaseModel):
    m1: float | None = Field(description="Maths 1 score")
    m2: float | None = Field(description="Maths 2 score")
    m3: float | None = Field(description="Maths 3 score")
    m4: float | None = Field(description="Maths 4 score")
    p1: float | None = Field(description="Physics 1 score")
    p2: float | None = Field(description="Physics 2 score")
    c1: float | None = Field(description="Chemistry 1 score")
    c2: float | None = Field(description="Chemistry 2 score")
    p_practicals: float | None = Field(description="Physics Practicals score")
    c_practicals: float | None = Field(description="Chemistry Practicals score")

class SSCMemoSchema(BaseModel):
    candidate_name: str | None = Field(description="Name of the candidate")
    father_name: str | None = Field(description="Name of the father")
    mother_name: str | None = Field(description="Name of the mother")
    date_of_birth: str | None = Field(description="Date of birth in DD/MM/YYYY")
    tenth_board_name: str | None = Field(description="Name of the educational board (e.g., CBSE, ICSE, State Board)")
    tenth_school_name: str | None = Field(description="Name of the school")
    tenth_hall_ticket_no: str | None = Field(description="Hall ticket or roll number")
    tenth_max_marks_cgpa: float | None = Field(description="Total maximum marks or CGPA possible")
    tenth_total_marks_cgpa: float | None = Field(description="Total marks or CGPA obtained")
    tenth_percentage: float | None = Field(description="Percentage scored")
    tenth_month_year: str | None = Field(description="Month and year of passing (e.g., March 2020)")
    identification_marks1: str | None = Field(description="Identification mark 1")
    identification_marks2: str | None = Field(description="Identification mark 2")
    district_code: str | None = Field(description="District code if available")

class TwelfthMemoSchema(BaseModel):
    board_name: str | None = Field(description="Name of the educational board")
    hall_ticket_number: str | None = Field(description="Hall ticket or candidate number")
    max_marks: float | None = Field(description="Maximum total marks")
    total_marks: float | None = Field(description="Total marks obtained")
    percentage: float | None = Field(description="Percentage scored")
    month_year: str | None = Field(description="Month and year of passing (e.g., March 2020)")
    district_code: str | None = Field(description="District code if available")
    subject_scores: SubjectScoresSchema | None = Field(description="Subject-wise scores if available")
