
import google.generativeai as genai
import json
from collections import defaultdict
import cx_Oracle




genai.configure(api_key="AIzaSyAR6uKmEVXEmjooLVglX8PwP5lstGb-Pwc")
model = genai.GenerativeModel('gemini-2.0-flash')


def run_query_from_intent(intent):
    
    user = "powerbi_user"
    password = "2m6BTrmC"
    dsn = "QSERVER2:1521/CCTL"

    conn = cx_Oracle.connect(user=user, password=password, dsn=dsn)
    cursor = conn.cursor()

    field_definitions = """
        Field definitions:
        - QTY_OH = Quantity Overhauled
        - QTY_RESERVED = Quantity Reserved

        Condition codes:
        GVI = Visual Inspected, SC = Scrap, OH = Overhauled, SV = Servicable, PRP = Partially Repaired,
        AR = As Removed, RP = Repairable, TEST = Tested, NE = New, NS = New Surplus,
        REP = Repaired, BER = Beyond Economical Repair, INSP = Inspected, MOD = Modified
        """


    try:
        action = intent.get("action")

        if action == "greeting":
            return "Hi! How can I help you explore inventory today?"
        
        elif action == "off_topic":
            return "I'm only able to help with inventory-related questions. How can I assist you with that?"
        
        elif action == "query":
            pn = intent.get("pn")
            fields = intent.get("fields") or [intent.get("field")]
            if not pn or not fields or fields == [None]:
                return "Invalid query: missing part number or field(s)."

            pn = pn.upper()

            if all(f.upper().startswith("QTY") for f in fields):
                sum_fields = [f"SUM({f}) AS {f}" for f in fields]
                select_clause = ", ".join(sum_fields)

                query = f"""
                    SELECT {select_clause}
                    FROM QCTL.STOCK
                    WHERE pn = :pn
                """
                print("Executing SQL:", query, "with:", {"pn": pn})
                cursor.execute(query, {"pn": pn})
                result = cursor.fetchone()

                if result:
                    data = {f: int(val) if val is not None else 0 for f, val in zip(fields, result)}
                    prompt = f"""{field_definitions}
        The following inventory summary was retrieved for part number {pn}:\n\n{json.dumps(data, indent=2)}\n\nGenerate a clear and user-friendly explanation using the correct field definitions in 1 line."""
                    gemini_response = model.generate_content(prompt)
                    return gemini_response.text
                else:
                    return f"No quantity records found for part number {pn}."

            join_condition_code = any(f.lower() in ["condition", "condition_code"] for f in fields)

            if join_condition_code and not any(f.upper().startswith("QTY") for f in fields):
                fields += ["QTY_OH", "QTY_RESERVED"]

            qty_fields = [f for f in fields if f.upper().startswith("QTY")]
            other_fields = [f for f in fields if not f.upper().startswith("QTY") and f.lower() not in ["condition", "condition_code"]]

            sum_select = [f"SUM(s.{f}) AS {f}" for f in qty_fields]
            non_sum_select = [f"s.{f}" for f in other_fields]

            if join_condition_code:
                non_sum_select.append("pcc.condition_code")

            select_clause = ", ".join(sum_select + non_sum_select)

            query = f"""
                SELECT {select_clause}
                FROM QCTL.STOCK s
                {"JOIN QCTL.part_condition_codes pcc ON s.pcc_auto_key = pcc.pcc_auto_key" if join_condition_code else ""}
                WHERE s.pn = :pn
                {"GROUP BY pcc.condition_code" if join_condition_code else ""}
            """
            print("Executing SQL:", query, "with:", {"pn": pn})
            cursor.execute(query, {"pn": pn})
            results = cursor.fetchall()

            if results:
                raw_data = []
                for row in results:
                    record = {}
                    i = 0

                    for f in qty_fields:
                        record[f] = int(row[i]) if row[i] is not None else 0
                        i += 1

                    for f in other_fields:
                        record[f] = row[i]
                        i += 1

                    if join_condition_code:
                        record["condition_code"] = row[i]
                        i += 1

                    raw_data.append(record)

                total_query = f"""
                    SELECT {", ".join([f"SUM({f}) AS total_{f}" for f in qty_fields])}
                    FROM QCTL.STOCK
                    WHERE pn = :pn
                """
                cursor.execute(total_query, {"pn": pn})
                total_result = cursor.fetchone()
                total_data = {
                    f"total_{qty_fields[i]}": int(val) if val is not None else 0
                    for i, val in enumerate(total_result)
                }

                prompt = f"""{field_definitions}
        Part number {pn} inventory summary by condition:\n
        {json.dumps(raw_data, indent=2)}

        Total quantities:\n
        {json.dumps(total_data, indent=2)}

        Summarize briefly in 1-2 lines showing each condition and its quantities with correct field definition, and also list the total quantities at the end. Use bullet points for each condition."""
                gemini_response = model.generate_content(prompt)
                return gemini_response.text
            else:
                return f"No records found for part number {pn}."
      



        elif action == "filter":
            field = intent.get("field")
            condition = intent.get("condition")
            value = intent.get("value")

            
            if field.upper().startswith("QTY"):
                query = f"""
                    SELECT pn, SUM({field}) AS total_{field}
                    FROM QCTL.STOCK
                    GROUP BY pn
                    HAVING SUM({field}) {condition} :val
                """
                print("Executing grouped SQL:", query, "with:", {"val": value})
                cursor.execute(query, {"val": value})
                results = cursor.fetchall()

                if results:
                    raw_data = [{"pn": r[0], f"total_{field}": int(r[1])} for r in results]
                    prompt = f"""{field_definitions}Parts where total {field} {condition} {value}:\n\n{json.dumps(raw_data, indent=2)}\n\nWrite a clean, markdown-formatted summary with each part listed as:- **Part Number**: value units Use bullet points and keep it readable for the user. using the correct field definitions."""
                    gemini_response = model.generate_content(prompt)
                    return gemini_response.text
                else:
                    return f"No parts found where total {field} {condition} {value}."
            else:
                query = f"SELECT pn, {field} FROM QCTL.STOCK WHERE {field} {condition} :val"
                print("Executing SQL:", query, "with:", {"val": value})
                cursor.execute(query, {"val": value})
                results = cursor.fetchall()

                if results:
                    raw_data = [{"pn": r[0], field: r[1]} for r in results]
                    prompt = f"""Parts where {field} {condition} {value}:\n\n{json.dumps(raw_data, indent=2)}\n\nWrite a clean, markdown-formatted summary with each part listed as:- **Part Number**: value units Use bullet points and keep it readable for the user. using the correct field definitions."""
                    gemini_response = model.generate_content(prompt)
                    return gemini_response.text
                else:
                    return f"No parts found where {field} {condition} {value}."


        elif action == "top":
            field = intent.get("field")
            limit = intent.get("limit") or 5  

            if not field or not field.upper().startswith("QTY"):
                return "Invalid field for top parts. Only quantity fields like QTY_OH, QTY_RESERVED are supported."

            query = f"""
                SELECT pn, SUM({field}) AS total_{field}
                FROM QCTL.STOCK
                GROUP BY pn
                ORDER BY total_{field} DESC
                FETCH FIRST {limit} ROWS ONLY
            """
            print("Executing SQL:", query)
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                raw_data = [{"pn": r[0], f"total_{field}": int(r[1]) if r[1] is not None else 0} for r in results]

                prompt = f"""{field_definitions}
        Top {limit} part numbers by total {field}:\n{json.dumps(raw_data, indent=2)}\nWrite a clean, markdown-formatted summary listing each part like:
        - **Part Number**: X units
        Use the correct field definitions and keep it readable for the user."""
                gemini_response = model.generate_content(prompt)
                return gemini_response.text
            else:
                return "No results found."

        
        elif action == "search_by_location":
            location = intent.get("location")
            if not location:
                return "Missing location for search."

            query = """
            SELECT 
                s.pn,
                TRIM(LOWER(s.description)) AS normalized_description, 
                SUM(s.QTY_OH) AS total_qty_oh, 
                SUM(s.QTY_RESERVED) AS total_qty_reserved
            FROM QCTL.STOCK s
            JOIN QCTL.location l ON s.loc_auto_key = l.loc_auto_key
            WHERE l.LOCATION_CODE = :loc
            GROUP BY s.pn, TRIM(LOWER(s.description))
            """
            cursor.execute(query, {"loc": location})
            results = cursor.fetchall()
            if results:
                grouped = defaultdict(lambda: defaultdict(lambda: {"total_qty_oh": 0, "total_qty_reserved": 0}))

                for r in results:
                    pn = r[0]
                    desc = r[1].strip().upper()
                    grouped[desc][pn]["total_qty_oh"] += int(r[2] or 0)
                    grouped[desc][pn]["total_qty_reserved"] += int(r[3] or 0)

                summary_lines = [f"**Inventory available in location {location.upper()}:**"]
                for desc, pn_dict in grouped.items():
                    summary_lines.append(f"\n**{desc}:**")
                    for pn, qtys in pn_dict.items():
                        summary_lines.append(f"- {pn}: {qtys['total_qty_oh']} available, {qtys['total_qty_reserved']} reserved")

                return "\n".join(summary_lines)
            else:
                return f"No parts found in location '{location}'."


        

        elif action == "search_description":    
            description = intent.get("keyword", "")
            if not description:
                return "Missing description for search."

            query = """
                SELECT 
                    pn, 
                    TRIM(LOWER(description)) AS normalized_description, 
                    SUM(QTY_OH) AS total_qty_oh, 
                    SUM(QTY_RESERVED) AS total_qty_reserved
                FROM QCTL.STOCK
                WHERE LOWER(description) LIKE :kw
                GROUP BY pn, TRIM(LOWER(description))
            """
            cursor.execute(query, {"kw": f"%{description.lower()}%"})
            results = cursor.fetchall()

            if results:
               
                grouped = defaultdict(lambda: defaultdict(lambda: {"total_qty_oh": 0, "total_qty_reserved": 0}))

                for r in results:
                    pn = r[0]
                    desc = r[1].strip().upper()
                    grouped[desc][pn]["total_qty_oh"] += int(r[2] or 0)
                    grouped[desc][pn]["total_qty_reserved"] += int(r[3] or 0)

                
                summary_lines = []
                for desc, pn_dict in grouped.items():
                    summary_lines.append(f"\n**{desc}:**")
                    for pn, qtys in pn_dict.items():
                        summary_lines.append(f"- {pn}: {qtys['total_qty_oh']} available, {qtys['total_qty_reserved']} reserved")

                return "\n".join(summary_lines)
            
            else:
                return f"No parts found with description containing '{description}'."



        else:
            return "Hi! How can I help you explore STOCK inventory today?"

    except cx_Oracle.DatabaseError as e:
        return f"Database error: {e}"

    finally:
        cursor.close()
        conn.close()
