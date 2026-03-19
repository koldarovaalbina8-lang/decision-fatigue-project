import csv
import json
import re
from pathlib import Path
from datetime import datetime, date
import streamlit as st

# ----------------------------
# Constants and fixed data
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
RESULT_JSON_FILE = BASE_DIR / "results.json"
RESULT_CSV_FILE = BASE_DIR / "results.csv"
RESULT_TXT_FILE = BASE_DIR / "results.txt"

OPTIONS = ["Never", "Rarely", "Sometimes", "Often", "Always"]
NORMAL_SCORES = [0, 1, 2, 3, 4]
REVERSE_SCORES = [4, 3, 2, 1, 0]

RESULT_BANDS = [
    (0, 13, "Mentally Clear"),
    (14, 26, "Mild Cognitive Load"),
    (27, 39, "Noticeable Decision Fatigue"),
    (40, 52, "High Mental Overload"),
    (53, 66, "Severe Cognitive Exhaustion"),
    (67, 80, "Critical Mental Drain")
]

FIXED_STATES = frozenset([
    "Mentally Clear",
    "Mild Cognitive Load",
    "Noticeable Decision Fatigue",
    "High Mental Overload",
    "Severe Cognitive Exhaustion",
    "Critical Mental Drain"
])

# tuple type explicitly used for assessment criteria
SAVE_FORMATS = ("TXT", "CSV", "JSON")

# set type explicitly used for assessment criteria
VALID_RESPONSE_VALUES = {1, 2, 3, 4, 5}


# ----------------------------
# Class for survey result
# ----------------------------
class SurveyResult:
    def __init__(
        self,
        full_name,
        date_of_birth,
        student_id,
        total_score,
        average_score,
        psychological_state,
        completed,
        completion_time
    ):
        self.full_name = full_name
        self.date_of_birth = date_of_birth
        self.student_id = student_id
        self.total_score = total_score
        self.average_score = average_score
        self.psychological_state = psychological_state
        self.completed = completed
        self.completion_time = completion_time

    def to_dict(self):
        return {
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth,
            "student_id": self.student_id,
            "total_score": self.total_score,
            "average_score": self.average_score,
            "psychological_state": self.psychological_state,
            "completed": self.completed,
            "completion_time": self.completion_time
        }


# ----------------------------
# Validation helpers
# ----------------------------
def validate_name(full_name):
    pattern = r"^[A-Za-z\s\-']+$"

    if len(full_name.strip()) < 3:
        return False, "Name is too short. Please try again."

    for char in full_name:
        if not (char.isalpha() or char.isspace() or char == "-" or char == "'"):
            return False, "Only letters, spaces, hyphens and apostrophes are allowed."

    if not re.match(pattern, full_name):
        return False, "Invalid name format. Please try again."

    return True, ""


def validate_student_id(student_id):
    if student_id.strip().isdigit():
        return True, ""
    return False, "Student ID must contain digits only."


def validate_questions(questions):
    if not isinstance(questions, list):
        return False

    if len(questions) < 15 or len(questions) > 25:
        return False

    for question_item in questions:
        if not isinstance(question_item, dict):
            return False
        if "question" not in question_item or "reverse" not in question_item:
            return False
        if not isinstance(question_item["question"], str):
            return False
        if not isinstance(question_item["reverse"], bool):
            return False

    return True


# explicit FOR loop for validation
def check_all_answered_for_loop(responses):
    for response in responses:
        if response is None:
            return False
        if response not in VALID_RESPONSE_VALUES:
            return False
    return True


# explicit WHILE loop for validation
def validate_responses_while_loop(responses):
    index = 0
    while index < len(responses):
        if responses[index] is None:
            return False
        index += 1
    return True


# ----------------------------
# File handling
# ----------------------------
def load_questions():
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as file:
            questions = json.load(file)

        if validate_questions(questions):
            return questions
        return []

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def save_result_json(result_data):
    try:
        with open(RESULT_JSON_FILE, "w", encoding="utf-8") as file:
            json.dump(result_data, file, indent=4)
        return True
    except OSError:
        return False


def save_result_csv(result_data):
    try:
        with open(RESULT_CSV_FILE, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["field", "value"])
            for key, value in result_data.items():
                writer.writerow([key, value])
        return True
    except OSError:
        return False


def save_result_txt(result_data):
    try:
        with open(RESULT_TXT_FILE, "w", encoding="utf-8") as file:
            for key, value in result_data.items():
                file.write(f"{key}: {value}\n")
        return True
    except OSError:
        return False


def save_result(result_data, format_choice):
    if format_choice == "TXT":
        return save_result_txt(result_data)
    elif format_choice == "CSV":
        return save_result_csv(result_data)
    elif format_choice == "JSON":
        return save_result_json(result_data)
    return False


def load_result_json():
    try:
        with open(RESULT_JSON_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def load_result_csv():
    try:
        with open(RESULT_CSV_FILE, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            rows = list(reader)

        if len(rows) < 2:
            return None

        result_data = {}
        for row in rows[1:]:
            if len(row) == 2:
                result_data[row[0]] = row[1]

        if "total_score" in result_data:
            result_data["total_score"] = int(result_data["total_score"])
        if "average_score" in result_data:
            result_data["average_score"] = float(result_data["average_score"])
        if "completed" in result_data:
            result_data["completed"] = result_data["completed"] == "True"

        return result_data

    except (FileNotFoundError, OSError, ValueError):
        return None


def load_result_txt():
    try:
        with open(RESULT_TXT_FILE, "r", encoding="utf-8") as file:
            lines = file.readlines()

        result_data = {}
        for line in lines:
            if ": " in line:
                key, value = line.strip().split(": ", 1)
                result_data[key] = value

        if not result_data:
            return None

        if "total_score" in result_data:
            result_data["total_score"] = int(result_data["total_score"])
        if "average_score" in result_data:
            result_data["average_score"] = float(result_data["average_score"])
        if "completed" in result_data:
            result_data["completed"] = result_data["completed"] == "True"

        return result_data

    except (FileNotFoundError, OSError, ValueError):
        return None


def load_result(selected_format):
    if selected_format == "TXT":
        return load_result_txt()
    elif selected_format == "CSV":
        return load_result_csv()
    elif selected_format == "JSON":
        return load_result_json()
    return None


# ----------------------------
# Survey logic
# ----------------------------
def get_question_score(is_reverse, user_choice):
    if is_reverse:
        return REVERSE_SCORES[user_choice - 1]
    return NORMAL_SCORES[user_choice - 1]


def interpret_score(score):
    for minimum, maximum, state in RESULT_BANDS:
        if minimum <= score <= maximum:
            return state
    return "Unknown State"


def display_result_web(data, title):
    st.subheader(title)
    st.write(f"**Full Name:** {data['full_name']}")
    st.write(f"**Date of Birth:** {data['date_of_birth']}")
    st.write(f"**Student ID:** {data['student_id']}")
    st.metric("Total Score", data["total_score"])
    st.metric("Average Score", data["average_score"])
    st.write(f"**Psychological State:** {data['psychological_state']}")
    st.write(f"**Completed:** {data['completed']}")
    st.write(f"**Completion Time:** {data['completion_time']}")


# ----------------------------
# Streamlit page
# ----------------------------
st.set_page_config(page_title="Decision Fatigue Survey", layout="centered")

st.title("Psychological Assessment System")
st.subheader("Decision Fatigue and Mental Overload Survey")
st.success("Please complete all fields before submitting.")

questions = load_questions()

if not questions:
    st.error("The survey cannot start because questions.json could not be loaded correctly.")
    st.stop()

tab1, tab2 = st.tabs(["Start New Questionnaire", "Load Existing Result"])

with tab1:
    st.write("Please fill in your details and answer all questions.")

    with st.form("survey_form"):
        st.subheader("Student Information")

        full_name = st.text_input("Enter surname and first name")
        dob = st.date_input(
            "Enter date of birth",
            value=None,
            min_value=date(1900, 1, 1),
            max_value=date.today()
        )
        student_id = st.text_input("Enter student ID number")

        st.subheader("Survey Questions")
        responses = []

        question_range = range(1, len(questions) + 1)

        for i in question_range:
            question_data = questions[i - 1]
            progress_value = i / len(questions)
            st.progress(progress_value, text=f"Progress: Question {i} of {len(questions)}")

            answer = st.radio(
                question_data["question"],
                options=[1, 2, 3, 4, 5],
                format_func=lambda x: f"{x}. {OPTIONS[x - 1]}",
                key=f"q_{i}",
                index=None
            )
            responses.append(answer)

        save_choice = st.selectbox("Choose save format", SAVE_FORMATS)
        submit_button = st.form_submit_button("Submit Questionnaire")

    if submit_button:
        valid_name, name_message = validate_name(full_name)
        valid_student_id, id_message = validate_student_id(student_id)

        if not valid_name:
            st.error(name_message)
        elif dob is None:
            st.error("Please select your date of birth.")
        elif not valid_student_id:
            st.error(id_message)
        elif not check_all_answered_for_loop(responses):
            st.error("Please answer all questions before submitting.")
        elif not validate_responses_while_loop(responses):
            st.error("Response validation failed.")
        else:
            with st.spinner("Calculating results..."):
                total_score = 0

                for question_data, response in zip(questions, responses):
                    score = get_question_score(question_data["reverse"], response)
                    total_score += score

                average_score = float(total_score) / len(questions)
                psychological_state = interpret_score(total_score)

            if psychological_state not in FIXED_STATES:
                st.error("Unexpected result state detected.")
            else:
                completed = True
                completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                survey_result = SurveyResult(
                    full_name=full_name.strip(),
                    date_of_birth=str(dob),
                    student_id=student_id.strip(),
                    total_score=total_score,
                    average_score=round(average_score, 2),
                    psychological_state=psychological_state,
                    completed=completed,
                    completion_time=completion_time
                )

                result_data = survey_result.to_dict()

                st.divider()
                display_result_web(result_data, "Survey Result")

                saved = save_result(result_data, save_choice)

                if saved:
                    st.success(f"Result saved successfully to {save_choice}.")
                else:
                    st.error("Error while saving the result.")

    if st.button("Reset Form"):
        st.rerun()

with tab2:
    st.subheader("Load Existing Result")
    load_format = st.selectbox("Choose file format to load", SAVE_FORMATS)

    if st.button("Load Result"):
        saved_data = load_result(load_format)

        if saved_data:
            st.divider()
            display_result_web(saved_data, "Loaded Result")
        else:
            st.error(f"No valid saved {load_format} result was found.")