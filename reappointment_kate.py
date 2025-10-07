import streamlit as st
import joblib
import pandas as pd
import datetime
import random # Need random for appointment ID

# Define the filename of your saved model
model_filename = 'readmission_risk_model.joblib'

# Load the trained model
try:
    model = joblib.load(model_filename)
    st.success("Readmission Risk Model loaded successfully!")
except FileNotFoundError:
    st.error(f"Error: Model file '{model_filename}' not found. Make sure it's in the same directory.")
    #st.stop() # Don't stop the app if model not found, just disable prediction

# --- Class Definitions (copied from the original notebook) ---
class Patient:
    def __init__(self, patient_id, name, phone_number, medical_history):
        self.patient_id = patient_id
        self.name = name
        self.phone_number = phone_number # Used for M-Pesa and reminders
        self.medical_history = medical_history
        self.vitals = [] # A list to store vitals logs
        self.appointments = []

    def __repr__(self):
        return f"Patient({self.name}, ID: {self.patient_id})"

class Doctor:
    def __init__(self, doctor_id, name, specialization):
        self.doctor_id = doctor_id
        self.name = name
        self.specialization = specialization
        self.appointments = []

    def __repr__(self):
        return f"Dr. {self.name} ({self.specialization})"

class Appointment:
    def __init__(self, appointment_id, patient, doctor, appointment_time):
        self.appointment_id = appointment_id
        self.patient = patient
        self.doctor = doctor
        self.appointment_time = appointment_time
        self.status = "Scheduled" # Can be "Completed" or "Cancelled"
        self.video_call_link = None # Will be generated later

    def __repr__(self):
        return f"Appointment({self.appointment_id} for {self.patient.name} with {self.doctor.name} at {self.appointment_time})"

class VitalsLog:
    def __init__(self, patient, log_time, data):
        self.patient = patient
        self.log_time = log_time
        self.data = data # e.g., {'blood_pressure': '120/80', 'blood_sugar': '5.5mmol/L'}

    def __repr__(self):
        return f"Vitals for {self.patient.name} at {self.log_time}: {self.data}"

# --- Simple In-Memory Database (for demonstration) ---
# In a real app, this would be a persistent database
if 'patients_db' not in st.session_state:
    st.session_state.patients_db = {}
if 'doctors_db' not in st.session_state:
    st.session_state.doctors_db = {}
if 'appointments_db' not in st.session_state:
    st.session_state.appointments_db = {}

# Add sample patient and doctor if not already present
if "PAT001" not in st.session_state.patients_db:
    st.session_state.patients_db["PAT001"] = Patient(patient_id="PAT001", name="Asha Wanjiru", phone_number="+254712345678", medical_history="Type 2 Diabetes")
if "DOC501" not in st.session_state.doctors_db:
     st.session_state.doctors_db["DOC501"] = Doctor(doctor_id="DOC501", name="John Omondi", specialization="Endocrinology")


# --- Core App Functions (adapted for Streamlit session state) ---
def schedule_appointment(patient_id, doctor_id, appointment_time):
    """Schedules a new appointment."""
    if patient_id not in st.session_state.patients_db or doctor_id not in st.session_state.doctors_db:
        return "Error: Patient or Doctor not found."

    patient = st.session_state.patients_db[patient_id]
    doctor = st.session_state.doctors_db[doctor_id]

    appointment_id = f"APP{random.randint(1000, 9999)}"
    new_appointment = Appointment(appointment_id, patient, doctor, appointment_time)

    st.session_state.appointments_db[appointment_id] = new_appointment
    patient.appointments.append(new_appointment)
    doctor.appointments.append(new_appointment)

    return new_appointment


# --- Streamlit App Interface ---
st.title("TibaSasa Healthcare App")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Readmission Risk Prediction", "Schedule Appointment", "View Appointments"])

if page == "Readmission Risk Prediction":
    st.header("Readmission Risk Prediction")
    st.write("Enter patient details to predict their readmission risk.")

    if 'model' in locals() and model: # Check if model was loaded successfully
        # Input widgets for patient data
        age = st.slider("Age", min_value=18, max_value=100, value=50)
        has_diabetes = st.checkbox("Has Diabetes")
        has_hypertension = st.checkbox("Has Hypertension")
        previous_admissions = st.number_input("Number of Previous Admissions", min_value=0, value=0)
        avg_blood_sugar_last_7_days = st.number_input("Average Blood Sugar (last 7 days, e.g., mmol/L)", min_value=0.0, value=5.0, format="%.2f")

        # Convert checkbox boolean to integer (0 or 1)
        has_diabetes_int = 1 if has_diabetes else 0
        has_hypertension_int = 1 if has_hypertension else 0

        # Button to trigger prediction
        if st.button("Predict Risk"):
            # Prepare the input data as a DataFrame
            patient_data = {
                'age': age,
                'has_diabetes': has_diabetes_int,
                'has_hypertension': has_hypertension_int,
                'previous_admissions': previous_admissions,
                'avg_blood_sugar_last_7_days': avg_blood_sugar_last_7_days
            }
            input_df = pd.DataFrame([patient_data])

            # Ensure the column order matches the training data
            features = ['age', 'has_diabetes', 'has_hypertension', 'previous_admissions', 'avg_blood_sugar_last_7_days']
            input_df = input_df[features]

            # Make the prediction
            risk_probability = model.predict_proba(input_df)[:, 1]
            risk_score = risk_probability[0]

            # Display the result
            st.subheader("Prediction Result:")
            st.write(f"The predicted readmission risk is: **{risk_score:.2f}**")

            # Provide a simple interpretation
            if risk_score > 0.5:
                st.warning("This patient has a higher predicted risk of readmission.")
            else:
                st.info("This patient has a lower predicted risk of readmission.")
    else:
        st.warning("Readmission risk prediction is unavailable because the model could not be loaded.")


elif page == "Schedule Appointment":
    st.header("Schedule Follow-up Appointment")

    # Simple dropdowns for patient and doctor (using sample data)
    patient_id_select = st.selectbox("Select Patient", list(st.session_state.patients_db.keys()), format_func=lambda x: st.session_state.patients_db[x].name)
    doctor_id_select = st.selectbox("Select Doctor", list(st.session_state.doctors_db.keys()), format_func=lambda x: st.session_state.doctors_db[x].name)

    # Date and time input
    appointment_date = st.date_input("Appointment Date", datetime.date.today())
    appointment_time = st.time_input("Appointment Time", datetime.datetime.now().time())

    # Combine date and time
    appointment_datetime = datetime.datetime.combine(appointment_date, appointment_time)

    if st.button("Schedule Appointment"):
        new_appointment = schedule_appointment(patient_id_select, doctor_id_select, appointment_datetime)
        if isinstance(new_appointment, Appointment):
            st.success(f"Appointment {new_appointment.appointment_id} scheduled for {new_appointment.patient.name} with {new_appointment.doctor.name} on {new_appointment.appointment_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.error(new_appointment) # Display error message

elif page == "View Appointments":
    st.header("Scheduled Appointments")

    if st.session_state.appointments_db:
        # Display appointments (simple table or list)
        appointments_list = []
        for app_id, app in st.session_state.appointments_db.items():
            appointments_list.append({
                "Appointment ID": app.appointment_id,
                "Patient": app.patient.name,
                "Doctor": app.doctor.name,
                "Time": app.appointment_time.strftime('%Y-%m-%d %H:%M'),
                "Status": app.status
            })
        st.table(pd.DataFrame(appointments_list))
    else:
        st.info("No appointments scheduled yet.")