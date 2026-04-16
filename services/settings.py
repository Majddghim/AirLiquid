from tools.database_tools import DatabaseTools


class SettingsService:
    def __init__(self):
        self.db = DatabaseTools()

    # ------------------------------------------------------------------ #
    # BRANDS                                                               #
    # ------------------------------------------------------------------ #

    def get_all_brands(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("SELECT id, name FROM car_brands ORDER BY name ASC")
            return cursor.fetchall()
        finally:
            con.close()

    def add_brand(self, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("INSERT INTO car_brands (name) VALUES (%s)", (name,))
            con.commit()
        finally:
            con.close()

    def update_brand(self, brand_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("UPDATE car_brands SET name=%s WHERE id=%s", (name, brand_id))
            con.commit()
        finally:
            con.close()

    def delete_brand(self, brand_id):
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("DELETE FROM car_models WHERE brand_id=%s", (brand_id,))
            cursor.execute("DELETE FROM car_brands WHERE id=%s", (brand_id,))
            con.commit()
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # MODELS                                                               #
    # ------------------------------------------------------------------ #

    def add_model(self, brand_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("INSERT INTO car_models (brand_id, name) VALUES (%s, %s)", (brand_id, name))
            con.commit()
        finally:
            con.close()

    def update_model(self, model_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("UPDATE car_models SET name=%s WHERE id=%s", (name, model_id))
            con.commit()
        finally:
            con.close()

    def delete_model(self, model_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("DELETE FROM car_models WHERE id=%s", (model_id,))
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # DÉPARTEMENTS                                                         #
    # ------------------------------------------------------------------ #

    def add_departement(self, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("INSERT INTO departements (name) VALUES (%s)", (name,))
            con.commit()
        finally:
            con.close()

    def update_departement(self, dept_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("UPDATE departements SET name=%s WHERE id=%s", (name, dept_id))
            con.commit()
        finally:
            con.close()

    def delete_departement(self, dept_id):
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("DELETE FROM postes WHERE departement_id=%s", (dept_id,))
            cursor.execute("DELETE FROM departements WHERE id=%s", (dept_id,))
            con.commit()
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # POSTES                                                               #
    # ------------------------------------------------------------------ #

    def add_poste(self, departement_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("INSERT INTO postes (departement_id, name) VALUES (%s, %s)", (departement_id, name))
            con.commit()
        finally:
            con.close()

    def update_poste(self, poste_id, name):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("UPDATE postes SET name=%s WHERE id=%s", (name, poste_id))
            con.commit()
        finally:
            con.close()

    def delete_poste(self, poste_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("DELETE FROM postes WHERE id=%s", (poste_id,))
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # CAR PARTS                                                            #
    # ------------------------------------------------------------------ #

    def get_all_parts(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, name, category, alert_km_interval, alert_month_interval, notes
                FROM car_parts ORDER BY category ASC, name ASC
            """)
            return cursor.fetchall()
        finally:
            con.close()

    def add_part(self, name, category, alert_km_interval, alert_month_interval, notes):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO car_parts (name, category, alert_km_interval, alert_month_interval, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, category or None, alert_km_interval or None, alert_month_interval or None, notes or None))
            con.commit()
        finally:
            con.close()

    def update_part(self, part_id, name, category, alert_km_interval, alert_month_interval, notes):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                UPDATE car_parts SET
                    name=%s, category=%s, alert_km_interval=%s,
                    alert_month_interval=%s, notes=%s
                WHERE id=%s
            """, (name, category or None, alert_km_interval or None, alert_month_interval or None, notes or None, part_id))
            con.commit()
        finally:
            con.close()

    def delete_part(self, part_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("DELETE FROM car_parts WHERE id=%s", (part_id,))
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # GARAGES                                                              #
    # ------------------------------------------------------------------ #

    def get_all_garages(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, name, type, brand, phone, address, contact_person, status
                FROM garages ORDER BY name ASC
            """)
            return cursor.fetchall()
        finally:
            con.close()

    def add_garage(self, name, type_, brand, phone, address, contact_person):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO garages (name, type, brand, phone, address, contact_person)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, type_ or 'independent', brand or None, phone or None, address or None, contact_person or None))
            con.commit()
        finally:
            con.close()

    def update_garage(self, garage_id, name, type_, brand, phone, address, contact_person, status):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                UPDATE garages SET
                    name=%s, type=%s, brand=%s, phone=%s,
                    address=%s, contact_person=%s, status=%s
                WHERE id=%s
            """, (name, type_ or 'independent', brand or None, phone or None,
                  address or None, contact_person or None, status or 'active', garage_id))
            con.commit()
        finally:
            con.close()
    def delete_garage(self, garage_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("UPDATE garages SET status='inactive' WHERE id=%s", (garage_id,))
            con.commit()
        finally:
            con.close()