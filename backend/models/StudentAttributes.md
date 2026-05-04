# Student Model Attributes

Below are the attributes defined in the `Student` model (Pydantic `BaseModel`) in `backend/models/StudentModel.py`.

### Core Information
| Attribute | Type |
|-----------|------|
| `degree_code` | `Optional[str]` |
| `ht_no` | `Optional[str]` |
| `student_name` | `Optional[str]` |
| `father_name` | `Optional[str]` |
| `mother_name` | `Optional[str]` |
| `date_of_birth` | `Optional[str]` |
| `gender` | `Optional[str]` |
| `identification_mark_1` | `Optional[str]` |
| `identification_mark_2` | `Optional[str]` |

### 10th Class details
| Attribute | Type |
|-----------|------|
| `tenth_board_name` | `Optional[str]` |
| `tenth_school_name` | `Optional[str]` |
| `tenth_district_code` | `Optional[str]` |
| `tenth_ht_no` | `Optional[str]` |
| `tenth_maximum_marks` | `Optional[str]` |
| `tenth_total_marks_cgpa` | `Optional[str]` |
| `tenth_percentage` | `Optional[str]` |
| `tenth_month_year` | `Optional[str]` |

### 12th Class details
| Attribute | Type |
|-----------|------|
| `twelfth_board_name` | `Optional[str]` |
| `twelfth_college_name` | `Optional[str]` |
| `twelfth_district_code` | `Optional[str]` |
| `twelfth_ht_no` | `Optional[str]` |
| `twelfth_maximum_marks` | `Optional[str]` |
| `twelfth_total_marks` | `Optional[str]` |
| `twelfth_percentage` | `Optional[str]` |
| `twelfth_groups_percentage` | `Optional[str]` |
| `twelfth_month_year` | `Optional[str]` |

### Intermediate Marks (Group Subjects)
| Attribute | Type |
|-----------|------|
| `m1`, `m2`, `m3`, `m4` | `Optional[str]` |
| `p1`, `p2` | `Optional[str]` |
| `ch1`, `ch2` | `Optional[str]` |
| `plab`, `chlab` | `Optional[str]` |
| `total` | `Optional[str]` |

### Competitive Exam ranks
| Attribute | Type |
|-----------|------|
| `eapcet_ht_no` | `Optional[str]` |
| `eapcet_rank` | `Optional[str]` |
| `jee_ht_no` | `Optional[str]` |
| `jee_mains_rank` | `Optional[str]` |

### Contact Information
| Attribute | Type |
|-----------|------|
| `aadhaar_card_number` | `Optional[str]` |
| `mother_tongue` | `Optional[str]` |
| `student_phone` | `Optional[str]` |
| `parent_phone` | `Optional[str]` |
| `parent_email` | `Optional[str]` |
| `father_phone` | `Optional[str]` |
| `mother_phone` | `Optional[str]` |
| `vnr_email` | `Optional[str]` |
| `student_email` | `Optional[str]` |
| `father_email` | `Optional[str]` |
| `mother_email` | `Optional[str]` |

### Family & Social details
| Attribute | Type |
|-----------|------|
| `student_passport_no` | `Optional[str]` |
| `father_passport_no` | `Optional[str]` |
| `mother_passport_no` | `Optional[str]` |
| `father_profession_and_designation` | `Optional[str]` |
| `mother_profession_and_designation` | `Optional[str]` |
| `reservation` | `Optional[str]` |
| `category_name` | `Optional[str]` |
| `caste_as_per_tc` | `Optional[str]` |
| `ebc_status` | `Optional[str]` |
| `ews_status` | `Optional[str]` |
| `income` | `Optional[str]` |
| `blood_group` | `Optional[str]` |
| `nationality` | `Optional[str]` |
| `religion` | `Optional[str]` |
| `minority` | `Optional[str]` |

### Address Details
| Attribute | Type |
|-----------|------|
| `address_dno` | `Optional[str]` |
| `address_street` | `Optional[str]` |
| `address_village_town` | `Optional[str]` |
| `address_mandal` | `Optional[str]` |
| `address_district` | `Optional[str]` |
| `address_state` | `Optional[str]` |
| `address_pincode` | `Optional[str]` |
| `rural_urban` | `Optional[str]` |

### Enrollment details
| Attribute | Type |
|-----------|------|
| `admission_category` | `Optional[str]` |
| `program_level` | `Optional[str]` |
| `section` | `Optional[str]` |
| `branch_code` | `Optional[str]` |
| `college_code` | `Optional[str]` |
| `ph_status` | `Optional[str]` |
| `scribe` | `Optional[str]` |
| `status` | `Optional[str]` |
| `student_type` | `Optional[str]` |
| `Time_updated` | `Optional[datetime]` |

### Document Links
| Attribute | Type |
|-----------|------|
| `candidate_pic` | `Optional[str]` |
| `allotment_order` | `Optional[str]` |
| `joining_report` | `Optional[str]` |
| `aadhaar_link` | `Optional[str]` |
| `transfer_certificate_link` | `Optional[str]` |
| `tenth_memo_link` | `Optional[str]` |
| `twelfth_memo_link` | `Optional[str]` |
| `jee_rank_card_link` | `Optional[str]` |
| `eapcet_rank_card_link` | `Optional[str]` |
