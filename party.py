import pandas as pd
import io
import random

# --- Input Data ---
csv_data = """DATE,SHEEP,GOAT,TOTAL
1-Mar-2025,400,180,580
2-Mar-2025,520,250,770
3-Mar-2025,300,110,410
4-Mar-2025,670,290,960
5-Mar-2025,580,240,820
6-Mar-2025,710,210,920
7-Mar-2025,450,180,630
8-Mar-2025,600,300,900
9-Mar-2025,520,260,780
10-Mar-2025,750,190,940
11-Mar-2025,620,370,990
12-Mar-2025,430,200,630
13-Mar-2025,800,290,1090
14-Mar-2025,630,270,900
15-Mar-2025,470,180,650
16-Mar-2025,510,260,770
17-Mar-2025,880,310,1190
18-Mar-2025,530,230,760
19-Mar-2025,770,300,1070
20-Mar-2025,500,290,790
21-Mar-2025,620,275,895
22-Mar-2025,900,300,1200
23-Mar-2025,640,220,860
24-Mar-2025,580,260,840
25-Mar-2025,810,380,1190
26-Mar-2025,670,240,910
27-Mar-2025,620,270,890
28-Mar-2025,700,280,980
29-Mar-2025,430,295,725
30-Mar-2025,760,285,1045
31-Mar-2025,530,290,820
"""

df = pd.read_csv(io.StringIO(csv_data))

# --- Parameters ---
num_parties = 40
party_names = [f"Demo Party {i+1}" for i in range(num_parties)]
prices = {'Sheep': 4500, 'Goat': 4800}

# --- Initialization ---
party_assignments = {name: [] for name in party_names}

# --- Distribution Logic ---
items_to_distribute = ['Sheep', 'Goat']

for item in items_to_distribute:
    price = prices[item]
    for index, row in df.iterrows():
        date = row['DATE']
        daily_qty = row[item]

        if daily_qty <= 0:
            continue

        # Decide how many parties share this day's stock (min 2, max 5, or fewer if total parties < 5)
        max_split = min(num_parties, 5)
        min_split = min(num_parties, 2)
        num_splits = random.randint(min_split, max_split)

        # Select unique parties randomly
        selected_parties = random.sample(party_names, num_splits)

        # Distribute quantity
        assigned_so_far = 0
        for i in range(num_splits):
            party = selected_parties[i]
            if i == num_splits - 1:
                # Assign the remainder to the last party
                qty_to_assign = daily_qty - assigned_so_far
            else:
                # Assign roughly equal shares, ensuring integer amounts
                share = daily_qty // num_splits
                # Add some randomness: +/- up to 20% of the share, but not less than 1
                variation = int(share * random.uniform(-0.2, 0.2)) if share > 5 else 0
                qty_to_assign = max(1, share + variation)
                 # Don't assign more than remaining
                qty_to_assign = min(qty_to_assign, daily_qty - assigned_so_far)
                # Avoid assigning 0 if possible when others are left
                if qty_to_assign == 0 and (daily_qty - assigned_so_far) > 0 and i < num_splits -1:
                    qty_to_assign = 1


            if qty_to_assign > 0 :
                 party_assignments[party].append({
                    'Date': date,
                    'Item': item,
                    'Qty': qty_to_assign,
                    'Price (₹)': price,
                    'Amount (₹)': qty_to_assign * price
                 })
                 assigned_so_far += qty_to_assign
            # Handle potential floating point issues or if initial calculation leads to excess assignment
            if assigned_so_far > daily_qty:
                 # Find the last assignment and adjust it down
                 diff = assigned_so_far - daily_qty
                 if party_assignments[party][-1]['Qty'] >= diff:
                     party_assignments[party][-1]['Qty'] -= diff
                     party_assignments[party][-1]['Amount (₹)'] -= diff * price
                     assigned_so_far -= diff
                 # If the last assignment was too small, this indicates a logic flaw, but try to fix
                 # This part is complex error handling, ideally the logic prevents this.
                 # For simplicity, we'll assume the split logic works correctly to sum to daily_qty

        # Assertion check (optional): Ensure full day's quantity was assigned
        # day_total_assigned = sum(p['Qty'] for p_list in party_assignments.values() for p in p_list if p['Date'] == date and p['Item'] == item)
        # if day_total_assigned != row[item]:
        #     print(f"Warning: Mismatch on {date} for {item}. Expected {row[item]}, Assigned {day_total_assigned}")


# --- Format Output ---
output_string = ""
total_distributed_sheep = 0
total_distributed_goat = 0
grand_total_amount = 0

for party_name in party_names:
    assignments = party_assignments[party_name]
    if not assignments: # Skip parties with no assignments
        continue

    output_string += f"Party\t{party_name}\n"
    output_string += f"Date\tItem\tQty\tPrice (₹)\tAmount (₹)\n"

    party_total_qty = 0
    party_total_amount = 0

    # Sort assignments by date for readability
    assignments.sort(key=lambda x: pd.to_datetime(x['Date'], format='%d-%b-%Y'))

    for assign in assignments:
        output_string += f"{assign['Date']}\t{assign['Item']}\t{assign['Qty']}\t{assign['Price (₹)']}\t{assign['Amount (₹)']}\n"
        party_total_qty += assign['Qty']
        party_total_amount += assign['Amount (₹)']
        if assign['Item'] == 'Sheep':
            total_distributed_sheep += assign['Qty']
        else:
            total_distributed_goat += assign['Qty']

    output_string += f"\t\t{party_total_qty}\t\t{party_total_amount}\n"
    output_string += "\n\n" # Add space between parties
    grand_total_amount += party_total_amount

# --- Verification (Optional) ---
original_total_sheep = df['SHEEP'].sum()
original_total_goat = df['GOAT'].sum()

output_string += "--- Verification ---\n"
output_string += f"Original Total Sheep: {original_total_sheep}\n"
output_string += f"Distributed Total Sheep: {total_distributed_sheep}\n"
output_string += f"Original Total Goat: {original_total_goat}\n"
output_string += f"Distributed Total Goat: {total_distributed_goat}\n"
output_string += f"Grand Total Amount Distributed: {grand_total_amount}\n"
output_string += "--------------------\n"

# --- Print Output ---
print(output_string)

# Recalculate totals directly from the final assignments for accuracy check
final_check_sheep = sum(p['Qty'] for p_list in party_assignments.values() for p in p_list if p['Item'] == 'Sheep')
final_check_goat = sum(p['Qty'] for p_list in party_assignments.values() for p in p_list if p['Item'] == 'Goat')

if final_check_sheep != original_total_sheep or final_check_goat != original_total_goat:
     print("\n!!! WARNING: Discrepancy detected between original totals and final distributed totals after processing. Please review distribution logic. !!!")
     print(f"Original Sheep: {original_total_sheep}, Final Assigned Sheep: {final_check_sheep}")
     print(f"Original Goat: {original_total_goat}, Final Assigned Goat: {final_check_goat}")