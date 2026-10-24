"""Generator script to produce ~60 original generic synthetic standard rental clauses."""

from pathlib import Path

CLAUSES: list[dict[str, str]] = [
    {
        "filename": "abandonment_01_definition.md",
        "topic": "abandonment",
        "title": "Statutory Definition of Abandonment",
        "text": (
            "An unexcused absence of the Tenant from the premises for fourteen consecutive "
            "days while rent remains unpaid shall be deemed a legal abandonment of the "
            "leasehold estate. "
        ).strip(),
    },
    {
        "filename": "abandonment_02_property_storage.md",
        "topic": "abandonment",
        "title": "Handling of Abandoned Property",
        "text": (
            "Any personal property left behind by the Tenant following lease termination or "
            "abandonment may be stored by the Landlord for thirty days, after which it may be "
            "sold or disposed of as provided by law. "
        ).strip(),
    },
    {
        "filename": "alterations_01_no_modifications.md",
        "topic": "alterations",
        "title": "Prohibition of Structural Alterations",
        "text": (
            "The Tenant shall not repaint, wallpaper, alter electrical fixtures, or install "
            "permanent shelving or wall anchors without first obtaining the Landlord's "
            "written authorization. "
        ).strip(),
    },
    {
        "filename": "alterations_02_lock_changes.md",
        "topic": "alterations",
        "title": "Lock Alterations and Duplicate Keys",
        "text": (
            "The Tenant shall not alter, replace, or add locks or deadbolts to any exterior "
            "entrance door without the Landlord's consent, and must immediately provide a "
            "working master duplicate key. "
        ).strip(),
    },
    {
        "filename": "alterations_03_smoke_detectors.md",
        "topic": "alterations",
        "title": "Smoke Detector Testing Obligations",
        "text": (
            "The Tenant agrees to test operational smoke and carbon monoxide detectors on a "
            "monthly schedule and shall promptly replace drained batteries or report hardware "
            "defects to the Landlord. "
        ).strip(),
    },
    {
        "filename": "deposit_01_amount.md",
        "topic": "deposit",
        "title": "Security Deposit Obligation",
        "text": (
            "Upon execution of this Agreement, the Tenant shall deposit with the Landlord a "
            "sum equal to one month's rent as security for the faithful performance of all "
            "covenants and conditions herein. "
        ).strip(),
    },
    {
        "filename": "deposit_02_return_timeline.md",
        "topic": "deposit",
        "title": "Return of Security Deposit",
        "text": (
            "Within thirty days following the complete vacation and surrender of the "
            "premises, the Landlord shall return the security deposit together with an "
            "itemized statement of any lawful deductions. "
        ).strip(),
    },
    {
        "filename": "deposit_03_permitted_deductions.md",
        "topic": "deposit",
        "title": "Permitted Deductions from Deposit",
        "text": (
            "The Landlord may deduct from the security deposit amounts reasonably necessary "
            "to cover unpaid rent, unpaid utility charges, and the cost of repairing damage "
            "beyond normal wear and tear. "
        ).strip(),
    },
    {
        "filename": "deposit_04_no_last_month_rent.md",
        "topic": "deposit",
        "title": "Deposit Not Applicable to Last Month Rent",
        "text": (
            "The security deposit shall not be applied by the Tenant as payment for rent for "
            "the final month of the tenancy or for any other preceding installment of rent. "
        ).strip(),
    },
    {
        "filename": "deposit_05_holding_account.md",
        "topic": "deposit",
        "title": "Deposit Holding in Escrow",
        "text": (
            "The Landlord shall maintain the security deposit in an identifiable trust or "
            "escrow account at a federally insured financial institution, separate from "
            "operating and personal funds. "
        ).strip(),
    },
    {
        "filename": "entire_agreement_01_clause.md",
        "topic": "general",
        "title": "Entire Agreement Integration",
        "text": (
            "This Agreement constitutes the entire agreement between the parties with respect "
            "to the subject matter hereof. No oral representations, promises, or amendments "
            "shall be binding unless in writing. "
        ).strip(),
    },
    {
        "filename": "entry_01_notice_period.md",
        "topic": "entry_notice",
        "title": "Advance Notice for Landlord Entry",
        "text": (
            "Except in cases of genuine emergency, the Landlord shall give the Tenant at "
            "least twenty-four hours advance written notice of intention to enter the "
            "premises for routine inspections or repairs. "
        ).strip(),
    },
    {
        "filename": "entry_02_reasonable_hours.md",
        "topic": "entry_notice",
        "title": "Entry During Reasonable Business Hours",
        "text": (
            "All non-emergency inspections, maintenance visits, and contractor visits shall "
            "occur during normal business hours between 8:00 AM and 6:00 PM, Monday through "
            "Saturday. "
        ).strip(),
    },
    {
        "filename": "entry_03_showings.md",
        "topic": "entry_notice",
        "title": "Showings to Prospective Occupants",
        "text": (
            "During the final thirty days of the tenancy term, the Landlord may enter upon "
            "reasonable advance notice to exhibit the dwelling unit to prospective tenants or "
            "purchasers. "
        ).strip(),
    },
    {
        "filename": "entry_04_non_interference.md",
        "topic": "entry_notice",
        "title": "Non-Interference with Lawful Access",
        "text": (
            "The Tenant shall not unreasonably deny, obstruct, or delay access to the "
            "Landlord or authorized service personnel attempting lawful entry in accordance "
            "with this agreement. "
        ).strip(),
    },
    {
        "filename": "insurance_01_renters_insurance.md",
        "topic": "insurance",
        "title": "Renters Insurance Requirement",
        "text": (
            "The Tenant is advised and required to secure and maintain a comprehensive "
            "renter's insurance policy providing personal property coverage and at least "
            "$100,000 in general personal liability. "
        ).strip(),
    },
    {
        "filename": "insurance_02_landlord_nonliability.md",
        "topic": "insurance",
        "title": "Personal Property Loss Non-Liability",
        "text": (
            "The Landlord's property insurance does not insure the personal property, "
            "furniture, or effects of the Tenant against water intrusion, fire, theft, smoke, "
            "vandalism, or other casualty. "
        ).strip(),
    },
    {
        "filename": "late_fees_01_grace_period.md",
        "topic": "late_fees",
        "title": "Rent Payment Grace Period",
        "text": (
            "A grace period of five calendar days is permitted. Rent received by 11:59 PM on "
            "the fifth day of the month shall not be deemed delinquent. "
        ).strip(),
    },
    {
        "filename": "late_fees_02_amount.md",
        "topic": "late_fees",
        "title": "Late Charge Assessment",
        "text": (
            "If full rent is not received by the expiration of the grace period, the Tenant "
            "shall pay an additional late assessment fee of fifty dollars ($50.00) to cover "
            "administrative overhead. "
        ).strip(),
    },
    {
        "filename": "late_fees_03_returned_payment.md",
        "topic": "late_fees",
        "title": "Dishonored Check Charge",
        "text": (
            "For each payment check or electronic payment returned unpaid due to insufficient "
            "funds, the Tenant shall pay a processing fee of thirty-five dollars ($35.00) in "
            "addition to any applicable late fee. "
        ).strip(),
    },
    {
        "filename": "notices_01_delivery_method.md",
        "topic": "notices",
        "title": "Formal Notice Delivery",
        "text": (
            "Any legal notice required under this Agreement shall be in writing and served "
            "personally, sent by certified mail with return receipt requested, or delivered "
            "by confirmed electronic courier. "
        ).strip(),
    },
    {
        "filename": "occupancy_01_residential_use.md",
        "topic": "occupancy",
        "title": "Exclusive Residential Occupancy",
        "text": (
            "The leased premises shall be utilized exclusively as a private dwelling for "
            "residential living purposes and shall not be operated as a retail commercial "
            "space or daycare facility. "
        ).strip(),
    },
    {
        "filename": "occupancy_02_named_tenants.md",
        "topic": "occupancy",
        "title": "Limitation to Named Occupants",
        "text": (
            "The dwelling shall be occupied only by the individuals specifically identified "
            "as Tenants in this Agreement. Additional long-term occupants require written "
            "notification and approval. "
        ).strip(),
    },
    {
        "filename": "occupancy_03_illegal_activity.md",
        "topic": "occupancy",
        "title": "Prohibition of Unlawful Conduct",
        "text": (
            "The Tenant, family members, and guests shall not engage in, facilitate, or "
            "permit any unlawful, hazardous, or illicit drug-related activity on or near the "
            "leased property. "
        ).strip(),
    },
    {
        "filename": "pets_01_no_pets.md",
        "topic": "pets",
        "title": "General Pet Prohibition",
        "text": (
            "No animals, pets, birds, or reptiles of any kind shall be kept or harbored in or "
            "about the premises without the Landlord's prior written consent and an executed "
            "pet addendum. "
        ).strip(),
    },
    {
        "filename": "pets_02_assistance_animals.md",
        "topic": "pets",
        "title": "Service and Assistance Animals",
        "text": (
            "Qualified service animals and assistance animals required for individuals with "
            "verified disabilities are permitted without surcharge in compliance with "
            "applicable fair housing standards. "
        ).strip(),
    },
    {
        "filename": "pets_03_pet_deposit.md",
        "topic": "pets",
        "title": "Refundable Pet Deposit",
        "text": (
            "For authorized domestic pets, the Tenant shall pay a refundable pet security "
            "deposit of three hundred dollars ($300.00) to cover any potential animal-related "
            "odor or damage. "
        ).strip(),
    },
    {
        "filename": "quiet_enjoyment_01_covenant.md",
        "topic": "quiet_enjoyment",
        "title": "Covenant of Quiet Enjoyment",
        "text": (
            "The Landlord covenants that upon timely payment of rent and performance of "
            "obligations, the Tenant shall peaceably hold and enjoy the premises during the "
            "term without unlawful hindrance. "
        ).strip(),
    },
    {
        "filename": "quiet_enjoyment_02_noise.md",
        "topic": "quiet_enjoyment",
        "title": "Noise and Nuisance Prohibition",
        "text": (
            "The Tenant and all occupants shall not create or permit any excessive noise, "
            "loud music, vibration, or disruptive conduct that interferes with the peace, "
            "quiet, or comfort of neighboring residents. "
        ).strip(),
    },
    {
        "filename": "quiet_enjoyment_03_quiet_hours.md",
        "topic": "quiet_enjoyment",
        "title": "Designated Building Quiet Hours",
        "text": (
            "Strict quiet hours shall be observed throughout the premises and common areas "
            "between 10:00 PM and 7:00 AM on weekdays, and between 11:00 PM and 8:00 AM on "
            "weekends. "
        ).strip(),
    },
    {
        "filename": "renewal_01_extension_notice.md",
        "topic": "renewal",
        "title": "Notice of Intent to Renew",
        "text": (
            "The Tenant shall give the Landlord written notice of intention to renew or "
            "extend the tenancy at least sixty calendar days prior to the expiration of the "
            "initial term. "
        ).strip(),
    },
    {
        "filename": "renewal_02_holdover.md",
        "topic": "renewal",
        "title": "Unapproved Holdover Tenancy",
        "text": (
            "If the Tenant continues in possession after lease expiration without the "
            "Landlord's written agreement, the tenancy becomes month-to-month subject to rent "
            "equal to one hundred twenty percent of the prior rate. "
        ).strip(),
    },
    {
        "filename": "renewal_03_rent_adjustment.md",
        "topic": "renewal",
        "title": "Notice of Renewal Rent Increase",
        "text": (
            "The Landlord may propose an adjusted rental rate for a successor lease term by "
            "delivering written notice of the proposed adjustment at least forty-five days "
            "prior to term expiration. "
        ).strip(),
    },
    {
        "filename": "rent_01_due_date.md",
        "topic": "rent",
        "title": "Base Rent Payment Due Date",
        "text": (
            "The Tenant agrees to pay the Landlord a fixed base rent in advance on or before "
            "the first calendar day of each month during the term of this tenancy, without "
            "prior demand or setoff. "
        ).strip(),
    },
    {
        "filename": "rent_02_payment_method.md",
        "topic": "rent",
        "title": "Permitted Payment Methods",
        "text": (
            "Rent payments shall be made by electronic funds transfer, automated clearing "
            "house (ACH), personal check, or cashier's check through the Landlord's "
            "designated resident portal. "
        ).strip(),
    },
    {
        "filename": "rent_03_proration.md",
        "topic": "rent",
        "title": "Prorated First Month Rent",
        "text": (
            "If the lease commencement date falls on a day other than the first day of the "
            "calendar month, rent for the partial initial month shall be prorated based upon "
            "a thirty-day month. "
        ).strip(),
    },
    {
        "filename": "rent_04_no_setoff.md",
        "topic": "rent",
        "title": "Independent Covenant to Pay Rent",
        "text": (
            "The obligation to pay rent is an independent covenant. The Tenant shall not "
            "withhold or reduce rent payments on account of any alleged failure or dispute, "
            "except as expressly authorized by law. "
        ).strip(),
    },
    {
        "filename": "rent_05_place_of_payment.md",
        "topic": "rent",
        "title": "Designated Place of Payment",
        "text": (
            "All rent and other financial obligations under this agreement shall be delivered "
            "to the Landlord at the Landlord's official business address or via an authorized "
            "secure banking portal. "
        ).strip(),
    },
    {
        "filename": "repairs_01_landlord_duty.md",
        "topic": "repairs",
        "title": "Landlord Structural Maintenance Duty",
        "text": (
            "The Landlord agrees to maintain the foundations, exterior walls, roof, plumbing, "
            "heating, and electrical systems of the building in reasonably good working order "
            "and repair. "
        ).strip(),
    },
    {
        "filename": "repairs_02_tenant_duty.md",
        "topic": "repairs",
        "title": "Tenant Cleanliness and Sanitary Duty",
        "text": (
            "The Tenant covenants to keep the interior of the dwelling unit clean, safe, and "
            "sanitary, and to dispose of all organic waste and trash in a clean and orderly "
            "manner. "
        ).strip(),
    },
    {
        "filename": "repairs_03_notice_of_defects.md",
        "topic": "repairs",
        "title": "Written Notice of Defects",
        "text": (
            "The Tenant shall give prompt written notice to the Landlord of any plumbing "
            "leaks, electrical malfunctions, water intrusion, or other defective conditions "
            "requiring repair. "
        ).strip(),
    },
    {
        "filename": "repairs_04_emergency_access.md",
        "topic": "repairs",
        "title": "Emergency Access for Repairs",
        "text": (
            "In the event of an imminent emergency threatening life, safety, or structural "
            "damage, the Landlord or authorized agents may enter the premises immediately "
            "without prior notification. "
        ).strip(),
    },
    {
        "filename": "repairs_05_tenant_misuse.md",
        "topic": "repairs",
        "title": "Repairs Caused by Tenant Neglect",
        "text": (
            "The Tenant shall pay for the cost of repairing any damage caused by the willful "
            "misconduct, carelessness, misuse, or neglect of the Tenant, occupants, or "
            "visiting guests. "
        ).strip(),
    },
    {
        "filename": "rules_01_trash_disposal.md",
        "topic": "rules",
        "title": "Garbage and Refuse Handling",
        "text": (
            "All household garbage and refuse shall be enclosed in sanitary plastic bags and "
            "deposited directly into the outdoor communal dumpster or recycling carts "
            "provided for the property. "
        ).strip(),
    },
    {
        "filename": "rules_02_smoking.md",
        "topic": "rules",
        "title": "Smoke-Free Dwelling Policy",
        "text": (
            "Smoking, burning of incense, and vaping of tobacco or electronic nicotine "
            "products is strictly prohibited inside the leased unit, on enclosed porches, and "
            "in interior common areas. "
        ).strip(),
    },
    {
        "filename": "rules_03_balcony_use.md",
        "topic": "rules",
        "title": "Balcony and Patio Guidelines",
        "text": (
            "Balconies, decks, and exterior patios shall be kept tidy and unencumbered. Using "
            "balconies for storage or operating open-flame charcoal cooking grills is "
            "strictly prohibited. "
        ).strip(),
    },
    {
        "filename": "severability_01_clause.md",
        "topic": "general",
        "title": "Severability of Contractual Terms",
        "text": (
            "If any term, covenant, or condition of this Agreement is held to be invalid or "
            "unenforceable, the remaining provisions hereof shall remain in full force and "
            "effect without impairment. "
        ).strip(),
    },
    {
        "filename": "subletting_01_prior_consent.md",
        "topic": "subletting",
        "title": "Consent Required for Subletting",
        "text": (
            "The Tenant shall not assign, mortgage, or encumber this Agreement, nor sublet "
            "the whole or any portion of the leased premises without obtaining the Landlord's "
            "prior written consent. "
        ).strip(),
    },
    {
        "filename": "subletting_02_short_term_rental.md",
        "topic": "subletting",
        "title": "Short-Term Vacation Rental Prohibition",
        "text": (
            "Listing the premises or any part thereof on peer-to-peer lodging platforms, "
            "short-term rental networks, or home-sharing sites constitutes a substantial "
            "breach of tenancy and is strictly prohibited. "
        ).strip(),
    },
    {
        "filename": "subletting_03_guest_duration.md",
        "topic": "subletting",
        "title": "Guest Duration Restrictions",
        "text": (
            "Temporary overnight guests may not remain on the premises for more than fourteen "
            "cumulative calendar days within any six-month period without prior written "
            "approval from the Landlord. "
        ).strip(),
    },
    {
        "filename": "subletting_04_screening_costs.md",
        "topic": "subletting",
        "title": "Subtenant Screening Expenses",
        "text": (
            "If the Landlord evaluates a proposed subtenant or replacement occupant, the "
            "Tenant shall pay the reasonable and customary third-party background and credit "
            "verification fees incurred. "
        ).strip(),
    },
    {
        "filename": "termination_01_fixed_term.md",
        "topic": "termination",
        "title": "Expiration of Initial Lease Term",
        "text": (
            "This Agreement shall terminate automatically upon the expiration of the stated "
            "initial term, unless extended or renewed in writing signed by all parties prior "
            "to expiration. "
        ).strip(),
    },
    {
        "filename": "termination_02_month_to_month.md",
        "topic": "termination",
        "title": "Month-to-Month Termination Notice",
        "text": (
            "Either party may terminate a periodic month-to-month tenancy by serving a "
            "written notice of termination upon the other party at least thirty calendar days "
            "prior to the proposed termination date. "
        ).strip(),
    },
    {
        "filename": "termination_03_military.md",
        "topic": "termination",
        "title": "Military Orders Early Termination",
        "text": (
            "A Tenant who enters active military service or receives permanent change of "
            "station orders may terminate this lease early upon delivering written notice and "
            "a copy of official military orders. "
        ).strip(),
    },
    {
        "filename": "termination_04_early_termination_fee.md",
        "topic": "termination",
        "title": "Early Termination Consideration",
        "text": (
            "If the Tenant terminates this lease prior to the expiration date without "
            "statutory cause, the Tenant shall remain liable for rent until relet, or may pay "
            "an early termination fee equal to two months rent. "
        ).strip(),
    },
    {
        "filename": "termination_05_surrender_condition.md",
        "topic": "termination",
        "title": "Condition of Premises upon Surrender",
        "text": (
            "Upon termination, the Tenant shall surrender the premises in broom-clean "
            "condition, removing all personal property, trash, and returning all keys and "
            "access devices to the Landlord. "
        ).strip(),
    },
    {
        "filename": "utilities_01_tenant_responsibility.md",
        "topic": "utilities",
        "title": "Tenant Utility Accounts",
        "text": (
            "The Tenant agrees to establish service accounts and pay all charges for "
            "electricity, natural gas, cable television, internet, and telephone services "
            "utilized within the leased dwelling. "
        ).strip(),
    },
    {
        "filename": "utilities_02_landlord_responsibility.md",
        "topic": "utilities",
        "title": "Landlord Supplied Utilities",
        "text": (
            "The Landlord shall supply cold water, municipal wastewater sewer service, and "
            "residential trash removal from the centralized collection area at no additional "
            "expense to the Tenant. "
        ).strip(),
    },
    {
        "filename": "utilities_03_heat_minimum.md",
        "topic": "utilities",
        "title": "Minimum Temperature Maintenance",
        "text": (
            "During cold weather months, the Tenant shall maintain an interior temperature of "
            "at least 55 degrees Fahrenheit (13 degrees Celsius) to prevent freezing and "
            "bursting of domestic water pipes. "
        ).strip(),
    },
    {
        "filename": "utilities_04_interruption.md",
        "topic": "utilities",
        "title": "Non-Liability for Service Interruption",
        "text": (
            "The Landlord shall not be liable for damages or rent reduction resulting from "
            "temporary utility outages or service disruptions caused by weather, municipal "
            "maintenance, or force majeure. "
        ).strip(),
    },
]


def generate_baseline_pack(target_dir: Path) -> int:
    """Generate generic synthetic standard clauses in target directory."""
    target_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for clause in CLAUSES:
        file_path = target_dir / clause["filename"]
        header = (
            f"---\ntopic: {clause['topic']}\ntitle: {clause['title']}\n"
            f"jurisdiction: generic-synthetic\nsynthetic: true\n---\n"
        )
        content = f"{header}{clause['text']}\n"
        file_path.write_text(content, encoding="utf-8")
        count += 1
    return count


if __name__ == "__main__":
    pack_dir = Path(__file__).parent.parent / "baseline_packs" / "rental"
    total = generate_baseline_pack(pack_dir)
    print(f"Generated {total} standard clauses in {pack_dir}")
