"""
seed_hospital_doctors.py
Run once:  python seed_hospital_doctors.py

Populates the HospitalReferenceDoctor table with 100 Indian reference doctors.
These are NOT system accounts – they are only used for admin verification.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms_core.settings')
django.setup()

from accounts.models import HospitalReferenceDoctor

REFERENCE_DOCTORS = [
    # (Name, Department, HospitalDocID, Specialization)
    ("Dr. Arun Singh",          "Primary Care Doctor",              "HOSP-001", "Interventional Cardiology"),
    ("Dr. Priya Sharma",        "Internal Medicine Specialist",     "HOSP-002", "Epilepsy & Stroke"),
    ("Dr. Rohan Verma",         "Clinical Physician",               "HOSP-003", "Joint Replacement"),
    ("Dr. Neha Gupta",          "Family Medicine Doctor",           "HOSP-004", "Neonatology"),
    ("Dr. Amit Patel",          "Medical Officer",                  "HOSP-005", "Laparoscopic Surgery"),
    ("Dr. Sunita Rao",          "General Medicine Physician",       "HOSP-006", "Maternal-Fetal Medicine"),
    ("Dr. Vikram Joshi",        "Primary Care Doctor",              "HOSP-007", "Cosmetic Dermatology"),
    ("Dr. Kavita Nair",         "Internal Medicine Specialist",     "HOSP-008", "Retinal Surgery"),
    ("Dr. Rajesh Kumar",        "Clinical Physician",               "HOSP-009", "Child Psychiatry"),
    ("Dr. Anita Mehta",         "Family Medicine Doctor",           "HOSP-010", "Diabetes & Thyroid"),
    ("Dr. Sanjay Bose",         "Medical Officer",                  "HOSP-011", "Kidney Transplantation"),
    ("Dr. Pooja Sinha",         "General Medicine Physician",       "HOSP-012", "Breast Oncology"),
    ("Dr. Deepak Mishra",       "Primary Care Doctor",              "HOSP-013", "Critical Care"),
    ("Dr. Ritu Agarwal",        "Internal Medicine Specialist",     "HOSP-014", "Autoimmune Diseases"),
    ("Dr. Kiran Desai",         "Clinical Physician",               "HOSP-015", "Hepatology"),
    ("Dr. Mohan Pillai",        "Family Medicine Doctor",           "HOSP-016", "Urological Oncology"),
    ("Dr. Swati Chaudhary",     "Medical Officer",                  "HOSP-017", "Head & Neck Surgery"),
    ("Dr. Nitin Kapoor",        "General Medicine Physician",       "HOSP-018", "Interventional Radiology"),
    ("Dr. Meena Saxena",        "Primary Care Doctor",              "HOSP-019", "Pain Management"),
    ("Dr. Alok Tiwari",         "Internal Medicine Specialist",     "HOSP-020", "Trauma Surgery"),
    ("Dr. Shruti Banerjee",     "Clinical Physician",               "HOSP-021", "Electrophysiology"),
    ("Dr. Harish Menon",        "Family Medicine Doctor",           "HOSP-022", "Spine Surgery"),
    ("Dr. Geeta Pandey",        "Medical Officer",                  "HOSP-023", "High-Risk Obstetrics"),
    ("Dr. Suresh Iyer",         "General Medicine Physician",       "HOSP-024", "Reconstructive Surgery"),
    ("Dr. Lakshmi Reddy",       "Primary Care Doctor",              "HOSP-025", "Pediatric Cardiology"),
    ("Dr. Nandita Roy",         "Internal Medicine Specialist",     "HOSP-026", "Bone Marrow Transplant"),
    ("Dr. Varun Malhotra",      "Clinical Physician",               "HOSP-027", "Knee & Shoulder"),
    ("Dr. Parveen Arora",       "Family Medicine Doctor",           "HOSP-028", "Oral & Maxillofacial"),
    ("Dr. Divya Chauhan",       "Medical Officer",                  "HOSP-029", "Infectious Diseases"),
    ("Dr. Rajan Naik",          "General Medicine Physician",       "HOSP-030", "Endovascular Procedures"),
    ("Dr. Smita Kulkarni",      "Primary Care Doctor",              "HOSP-031", "Geriatric Psychiatry"),
    ("Dr. Gaurav Thakur",       "Internal Medicine Specialist",     "HOSP-032", "Valve Repair"),
    ("Dr. Rashmi Dutta",        "Clinical Physician",               "HOSP-033", "Movement Disorders"),
    ("Dr. Prakash Murthy",      "Family Medicine Doctor",           "HOSP-034", "Robotic Surgery"),
    ("Dr. Tanuja Bhatt",        "Medical Officer",                  "HOSP-035", "Psoriasis & Lupus"),
    ("Dr. Hemant Chavan",       "General Medicine Physician",       "HOSP-036", "Dialysis"),
    ("Dr. Suman Tripathi",      "Primary Care Doctor",              "HOSP-037", "Lung Cancer"),
    ("Dr. Vikrant Soni",        "Internal Medicine Specialist",     "HOSP-038", "MRI Diagnostics"),
    ("Dr. Deepa Goswami",       "Clinical Physician",               "HOSP-039", "Laparoscopic Gynecology"),
    ("Dr. Ashish Rawat",        "Family Medicine Doctor",           "HOSP-040", "Spine Disorders"),
    ("Dr. Pallavi Shukla",      "Medical Officer",                  "HOSP-041", "Pediatric Neurology"),
    ("Dr. Mahesh Garg",         "General Medicine Physician",       "HOSP-042", "Bariatric Surgery"),
    ("Dr. Shikha Aggarwal",     "Primary Care Doctor",              "HOSP-043", "Cochlear Implants"),
    ("Dr. Vinod Choudhary",     "Internal Medicine Specialist",     "HOSP-044", "Asthma & COPD"),
    ("Dr. Nisha Varma",         "Clinical Physician",               "HOSP-045", "Cataract Surgery"),
    ("Dr. Aditya Prasad",       "Family Medicine Doctor",           "HOSP-046", "Heart Failure"),
    ("Dr. Jayanti Bhardwaj",    "Medical Officer",                  "HOSP-047", "Obesity & Metabolic"),
    ("Dr. Rohit Dubey",         "General Medicine Physician",       "HOSP-048", "IBD & Crohn's"),
    ("Dr. Chanda Pathak",       "Primary Care Doctor",              "HOSP-049", "Spondyloarthritis"),
    ("Dr. Naveen Sampath",      "Internal Medicine Specialist",     "HOSP-050", "HIV & TB"),
    ("Dr. Kamala Subramanian",  "Clinical Physician",               "HOSP-051", "Fertility & IVF"),
    ("Dr. Sunil Pandita",       "Family Medicine Doctor",           "HOSP-052", "Brain Tumors"),
    ("Dr. Archana Lal",         "Medical Officer",                  "HOSP-053", "Coagulation Disorders"),
    ("Dr. Manish Srivastava",   "General Medicine Physician",       "HOSP-054", "Aortic Aneurysm"),
    ("Dr. Prachi Jain",         "Primary Care Doctor",              "HOSP-055", "Endodontics"),
    ("Dr. Bhavesh Trivedi",     "Internal Medicine Specialist",     "HOSP-056", "Burn Management"),
    ("Dr. Sangeeta Menon",      "Clinical Physician",               "HOSP-057", "Geriatric Medicine"),
    ("Dr. Kartik Bhattacharya", "Family Medicine Doctor",           "HOSP-058", "Pediatric Anaesthesia"),
    ("Dr. Ranjana Dwivedi",     "Medical Officer",                  "HOSP-059", "Colorectal Cancer"),
    ("Dr. Vivek Saxena",        "General Medicine Physician",       "HOSP-060", "Athletic Performance"),
    ("Dr. Anupama Hegde",       "Primary Care Doctor",              "HOSP-061", "Addiction Medicine"),
    ("Dr. Girish Yadav",        "Internal Medicine Specialist",     "HOSP-062", "Cardiac Rehabilitation"),
    ("Dr. Madhuri Pillai",      "Clinical Physician",               "HOSP-063", "Dermatopathology"),
    ("Dr. Sameer Khanna",       "Family Medicine Doctor",           "HOSP-064", "Pediatric Urology"),
    ("Dr. Anjali Sethia",       "Medical Officer",                  "HOSP-065", "Nuclear Medicine"),
    ("Dr. Pramod Wagh",         "General Medicine Physician",       "HOSP-066", "Trauma & Fractures"),
    ("Dr. Sunanda Iyengar",     "Primary Care Doctor",              "HOSP-067", "Headache & Migraine"),
    ("Dr. Rahul Bansode",       "Internal Medicine Specialist",     "HOSP-068", "Disaster Medicine"),
    ("Dr. Shobha Krishnamurthy","Clinical Physician",               "HOSP-069", "Urogynecology"),
    ("Dr. Nilesh Pawar",        "Family Medicine Doctor",           "HOSP-070", "Pancreatology"),
    ("Dr. Taruna Verma",        "Medical Officer",                  "HOSP-071", "Adolescent Medicine"),
    ("Dr. Akhilesh Sinha",      "General Medicine Physician",       "HOSP-072", "Lung Transplantation"),
    ("Dr. Preeti Saraswat",     "Primary Care Doctor",              "HOSP-073", "Adrenal Disorders"),
    ("Dr. Rajeev Kaushik",      "Internal Medicine Specialist",     "HOSP-074", "Hernia Surgery"),
    ("Dr. Vandana Malviya",     "Clinical Physician",               "HOSP-075", "Obstetric Anaesthesia"),
    ("Dr. Saurabh Deshpande",   "Family Medicine Doctor",           "HOSP-076", "Glomerulonephritis"),
    ("Dr. Ambika Natarajan",    "Medical Officer",                  "HOSP-077", "Cervical Cancer"),
    ("Dr. Piyush Rao",          "General Medicine Physician",       "HOSP-078", "Epilepsy Surgery"),
    ("Dr. Rekha Mitra",         "Primary Care Doctor",              "HOSP-079", "Hypertension"),
    ("Dr. Dinesh Buch",         "Internal Medicine Specialist",     "HOSP-080", "Sleep Medicine"),
    ("Dr. Leela Venkataraman",  "Clinical Physician",               "HOSP-081", "Lymphoma"),
    ("Dr. Shailesh Ghosh",      "Family Medicine Doctor",           "HOSP-082", "Peripheral Vascular"),
    ("Dr. Poornima Iyer",       "Medical Officer",                  "HOSP-083", "Normal & C-Section"),
    ("Dr. Abhijit Kulkarni",    "General Medicine Physician",       "HOSP-084", "Cleft Palate"),
    ("Dr. Jaya Nambiar",        "Primary Care Doctor",              "HOSP-085", "Gout & Crystal Arthritis"),
    ("Dr. Sudhir Tandon",       "Internal Medicine Specialist",     "HOSP-086", "Hair & Nail Disorders"),
    ("Dr. Madhav Chitale",      "Clinical Physician",               "HOSP-087", "Structural Heart Disease"),
    ("Dr. Rupa Sengupta",       "Family Medicine Doctor",           "HOSP-088", "Mood Disorders"),
    ("Dr. Ashok Bansal",        "Medical Officer",                  "HOSP-089", "Colorectal Surgery"),
    ("Dr. Sheela Krishnan",     "General Medicine Physician",       "HOSP-090", "Glaucoma"),
    ("Dr. Suhas Patil",         "Primary Care Doctor",              "HOSP-091", "Rhinology"),
    ("Dr. Alka Shinde",         "Internal Medicine Specialist",     "HOSP-092", "Pediatric Infectious Disease"),
    ("Dr. Baljit Singh",        "Clinical Physician",               "HOSP-093", "Arthroplasty"),
    ("Dr. Meghna Awasthi",      "Family Medicine Doctor",           "HOSP-094", "Breast Imaging"),
    ("Dr. Chandrakant More",    "Medical Officer",                  "HOSP-095", "Stone Disease"),
    ("Dr. Tara Ranganathan",    "General Medicine Physician",       "HOSP-096", "Cardiac Anaesthesia"),
    ("Dr. Vijay Parekh",        "Primary Care Doctor",              "HOSP-097", "Liver Transplant"),
    ("Dr. Namita Acharya",      "Internal Medicine Specialist",     "HOSP-098", "Dementia & Memory"),
    ("Dr. Lalit Rathore",       "Clinical Physician",               "HOSP-099", "Physiotherapy & Rehab"),
    ("Dr. Seema Bhave",         "Family Medicine Doctor",           "HOSP-100", "Paediatric Endocrinology"),
]


def seed():
    updated_count = 0
    created_count = 0
    for name, dept, doc_id, spec in REFERENCE_DOCTORS:
        obj, created = HospitalReferenceDoctor.objects.get_or_create(
            hospital_doc_id=doc_id,
            defaults={'name': name, 'department': dept, 'specialization': spec}
        )
        if created:
            created_count += 1
        else:
            # Update department (and other fields) even if doctor already exists
            obj.department = dept
            obj.name = name
            obj.specialization = spec
            obj.save()
            updated_count += 1

    print(f"[DONE] Created {created_count} new doctors, updated {updated_count} existing doctors.")
    total = HospitalReferenceDoctor.objects.count()
    print(f"[INFO] Total hospital reference doctors in DB: {total}")


if __name__ == '__main__':
    seed()
