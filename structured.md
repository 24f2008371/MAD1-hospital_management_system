# Project Structure and Analysis

## 1. Project Information

*   **Project Name:** Hospital Management System
*   **Purpose:** A web application to manage hospital operations, including doctors, patients, and appointments.
*   **Technologies Used:**
    *   **Backend:** Flask, Flask-SQLAlchemy, Flask-Login
    *   **Database:** SQLite
    *   **Frontend:** HTML, CSS, Bootstrap

## 2. Database Models

The project uses the following database models:

*   `User`: Stores user information, including username, password, and user type (admin, doctor, patient).
*   `Doctor`: Stores doctor-specific information, including name, email, department, and experience.
*   `Patient`: Stores patient-specific information, including name, phone number, and email.
*   `Department`: Stores department information.
*   `Appointment`: Stores appointment details, linking patients and doctors.
*   `Treatment`: Stores information about treatments provided during an appointment.

## 3. Existing Routes

The application currently has the following routes:

*   `/`: Landing page.
*   `/login`: User login.
*   `/register`: User registration.
*   `/admin`: Admin dashboard.
*   `/doctor`: Doctor dashboard.
*   `/patient`: Patient dashboard.
*   `/add_doctor`: Form for admins to add new doctors.
*   `/patient_history`: A page for patient history.
*   `/cardiology`, `/neurology`, `/oncology`, `/general`: Department-specific pages.

## 4. Pending Routes

Based on the database models and the existing routes, the following routes could be implemented:

*   **Admin:**
    *   `/admin/doctors`: View all doctors.
    *   `/admin/doctors/edit/<int:doctor_id>`: Edit a doctor's information.
    *   `/admin/doctors/delete/<int:doctor_id>`: Delete a doctor.
    *   `/admin/patients`: View all patients.
    *   `/admin/patients/edit/<int:patient_id>`: Edit a patient's information.
    *   `/admin/patients/delete/<int:patient_id>`: Delete a patient.
    *   `/admin/appointments`: View all appointments.
    *   `/admin/departments`: View all departments.
    *   `/admin/departments/add`: Add a new department.
    *   `/admin/departments/edit/<int:department_id>`: Edit a department.
    *   `/admin/departments/delete/<int:department_id>`: Delete a department.
*   **Doctor:**
    *   `/doctor/appointments`: View all appointments for the logged-in doctor.
    *   `/doctor/patients`: View all patients assigned to the logged-in doctor.
    *   `/doctor/profile`: View and edit the doctor's own profile.
*   **Patient:**
    *   `/patient/appointments`: View all appointments for the logged-in patient.
    *   `/patient/appointments/book`: Book a new appointment.
    *   `/patient/profile`: View and edit the patient's own profile.

## 5. CRUD Operations

### User Model

*   **Create:** New users can be created through the registration page.
*   **Read:** User information is read during login and for displaying user-specific information.
*   **Update:** User information can be updated in the user's profile.
*   **Delete:** Users can be deleted by an admin.

### Doctor Model

*   **Create:** New doctors can be created by an admin.
*   **Read:** Doctor information is displayed on the admin and doctor dashboards.
*   **Update:** Doctor information can be updated by an admin.
*   **Delete:** Doctors can be deleted by an admin.

### Patient Model

*   **Create:** New patients can be created through the registration page.
*   **Read:** Patient information is displayed on the admin and patient dashboards.
*   **Update:** Patient information can be updated by the patient or an admin.
*   **Delete:** Patients can be deleted by an admin.

### Department Model

*   **Create:** New departments can be created by an admin.
*   **Read:** Department information is displayed on the admin dashboard.
*   **Update:** Department information can be updated by an admin.
*   **Delete:** Departments can be deleted by an admin.

### Appointment Model

*   **Create:** New appointments can be created by patients.
*   **Read:** Appointment information is displayed on the admin, doctor, and patient dashboards.
*   **Update:** Appointment information can be updated by an admin or a doctor.
*   **Delete:** Appointments can be canceled by an admin, doctor, or patient.

### Treatment Model

*   **Create:** New treatments can be created by doctors.
*   **Read:** Treatment information is displayed on the patient's history page.
*   **Update:** Treatment information can be updated by doctors.
*   **Delete:** Treatments can be deleted by doctors.

## 6. Future Improvements

*   **Search Functionality:** Implement a search functionality to search for doctors, patients, and appointments.
*   **Email Notifications:** Send email notifications for appointment confirmations, reminders, and cancellations.
*   **Prescription Management:** Add a feature to manage prescriptions for patients.
*   **Billing and Invoicing:** Implement a billing and invoicing system.
*   **File Uploads:** Allow users to upload and store medical records and other documents.
*   **API:** Create a RESTful API to allow other applications to interact with the system.
*   **Testing:** Add unit and integration tests to ensure the application is working correctly.
