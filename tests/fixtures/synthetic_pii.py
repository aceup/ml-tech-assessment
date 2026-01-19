"""
Synthetic PII data for testing.

Contains realistic but fake PII for testing detection and anonymization.
"""

# Synthetic person names (clearly fake)
SYNTHETIC_NAMES = [
    "John Smith",
    "Sarah Johnson",
    "Michael Williams",
    "Emily Davis",
    "David Martinez",
    "Jennifer Garcia",
    "Robert Wilson",
    "Maria Rodriguez",
]

# Synthetic email addresses (invalid domains)
SYNTHETIC_EMAILS = [
    "john.smith@example.test",
    "sarah.j@testmail.invalid",
    "michael.w@fake-domain.test",
    "emily.davis@test-email.invalid",
]

# Synthetic phone numbers (555 prefix = not real)
SYNTHETIC_PHONES = [
    "555-123-4567",
    "(555) 234-5678",
    "555.345.6789",
    "1-555-456-7890",
]

# Synthetic SSNs (invalid test numbers)
SYNTHETIC_SSNS = [
    "123-45-6789",  # Test pattern
    "987-65-4321",
    "111-22-3333",
]

# Synthetic addresses
SYNTHETIC_ADDRESSES = [
    "123 Main Street, Test City, TC 12345",
    "456 Oak Avenue, Sample Town, ST 67890",
    "789 Pine Road, Example City, EC 54321",
]

# Medical record numbers (synthetic)
SYNTHETIC_MRNS = [
    "MRN-123456",
    "MRN-789012",
    "MRN-345678",
]


# Complete synthetic transcripts with PII
MEDICAL_TRANSCRIPT_WITH_PII = """
Patient: Sarah Johnson
DOB: 03/15/1985
Email: sarah.j@example.test
Phone: (555) 123-4567
SSN: 123-45-6789
MRN: MRN-123456

Chief Complaint: Follow-up consultation for treatment plan.

Notes:
Patient presented in good spirits and reported improvement in symptoms.
Discussed medication compliance and lifestyle modifications.
Patient's primary contact is spouse Michael Johnson at 555-234-5678.

Follow-up: Schedule appointment for next month. Send reminder to sarah.j@example.test.
"""

BUSINESS_TRANSCRIPT_WITH_PII = """
Coaching Session Notes
Client: John Smith
Email: john.smith@example.test
Phone: 555-345-6789
Company: Test Corp Inc.

Session Focus:
Discussed leadership development and team management strategies.
Client shared challenges with delegating to team members.
Contact information for team lead: Emily Davis (emily.davis@example.test).

Action Items:
1. Practice delegation with 2-3 tasks this week
2. Schedule team meeting
3. Follow up via email at john.smith@example.test

Next session: 2 weeks. Reminder sent to phone 555-345-6789.
"""

MINIMAL_PII_TRANSCRIPT = """
Today's coaching session with client went excellent.
We focused on leadership skills and goal-setting strategies.
The client made significant progress on quarterly objectives.
Next steps include team communication workshops and performance reviews.
"""

HEAVY_PII_TRANSCRIPT = """
Multi-client session notes:

Client 1: Sarah Johnson (sarah.j@example.test, SSN: 123-45-6789)
Address: 123 Main St, Test City, TC 12345
Phone: 555-123-4567

Client 2: Michael Williams (michael.w@fake-domain.test, SSN: 987-65-4321)
Address: 456 Oak Ave, Sample Town, ST 67890
Phone: (555) 234-5678

Client 3: Emily Davis (emily.davis@test-email.invalid, SSN: 111-22-3333)
Address: 789 Pine Rd, Example City, EC 54321
Phone: 555.345.6789

Group session covered confidential topics including:
- Personal financial information (Account #1234567890)
- Medical history discussions
- Family relationship details
- Credit card on file: 4532-1234-5678-9010
"""

# PII-free coaching transcript
CLEAN_COACHING_TRANSCRIPT = """
Executive Coaching Session Summary

Focus Areas:
- Strategic planning and organizational vision
- Leadership communication techniques
- Team performance optimization
- Change management strategies

Key Discussion Points:
The executive demonstrated strong understanding of delegation principles.
We explored various frameworks for decision-making under uncertainty.
Time management techniques were reviewed and action items established.

Outcomes:
- Clarity on quarterly priorities
- Framework for team restructuring
- Communication plan for stakeholders
- Performance metrics dashboard design

Next Session:
Continue progress on action items and review implementation results.
Focus on stakeholder engagement and measuring team productivity.
"""

# Edge cases
AMBIGUOUS_TEXT = """
John called about the project yesterday.
Mary sent an email with the updated timeline.
The address for the meeting is downtown.
Phone extension is 1234.
"""

UNICODE_WITH_PII = """
Patient Information (International):
Name: José García
Email: josé.garcía@example.test
Phone: +34-555-123-456
Address: Calle Principal 123, Madrid, España

Notes in multiple languages:
English: Follow-up appointment scheduled.
Spanish: Cita de seguimiento programada.
French: Rendez-vous de suivi programmé.
"""


def get_transcript_with_pii_count(count: int) -> str:
    """
    Generate transcript with specific number of PII entities.

    Args:
        count: Desired number of PII entities

    Returns:
        str: Synthetic transcript with approximately `count` PII entities
    """
    pii_items = []

    if count >= 1:
        pii_items.append(f"Name: {SYNTHETIC_NAMES[0]}")
    if count >= 2:
        pii_items.append(f"Email: {SYNTHETIC_EMAILS[0]}")
    if count >= 3:
        pii_items.append(f"Phone: {SYNTHETIC_PHONES[0]}")
    if count >= 4:
        pii_items.append(f"SSN: {SYNTHETIC_SSNS[0]}")
    if count >= 5:
        pii_items.append(f"Address: {SYNTHETIC_ADDRESSES[0]}")

    # Add more as needed
    for i in range(5, count):
        pii_items.append(f"Additional PII {i}: {SYNTHETIC_EMAILS[i % len(SYNTHETIC_EMAILS)]}")

    transcript = "Coaching session notes:\n" + "\n".join(pii_items)
    transcript += "\n\nSession covered leadership and communication skills."

    return transcript
