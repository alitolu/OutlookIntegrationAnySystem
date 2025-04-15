import pyodbc
from typing import Dict, List, Any
from .data_source import DataSource

class MSSQLHelper(DataSource):
    def __init__(self, config: Dict):
        if not isinstance(config, dict):
            raise ValueError("Config dictionary olmalıdır!")
            
        self.full_config = config 
        mssql_config = config.get("datasource", {}).get("mssql", {})
        
        required_fields = ['server', 'database', 'username', 'password']
        missing_fields = [field for field in required_fields if not mssql_config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Eksik MSSQL ayarları: {', '.join(missing_fields)}")
            
        self.config = mssql_config
        self.connection = None

        self.connection_string = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={mssql_config['server']};"
            f"DATABASE={mssql_config['database']};"
            f"UID={mssql_config['username']};"
            f"PWD={mssql_config['password']}"
        )
        
        if not self.connect():
            raise ConnectionError("MSSQL bağlantısı kurulamadı!")
        
        # Bağlantı havuzu ayarları
        self.connection_pool = []
        self.max_pool_size = 10  # Aynı anda max 10 bağlantı
        self.min_pool_size = 2   # En az 2 bağlantı hazır tut
        self.connection_timeout = 30  # 30 sn timeout
        
        # Başlangıç havuzunu oluştur
        self._initialize_pool()

    def _initialize_pool(self):
        """Başlangıç bağlantı havuzunu oluştur"""
        try:
            for _ in range(self.min_pool_size):
                conn = pyodbc.connect(
                    self.connection_string,
                    timeout=self.connection_timeout
                )
                self.connection_pool.append(conn)
            print(f"Bağlantı havuzu oluşturuldu (min:{self.min_pool_size})")
        except Exception as e:
            print(f"Havuz oluşturma hatası: {str(e)}")

    def connect(self) -> bool:
        """Tam bağlantı"""
        try:
            print("MSSQL Bağlantı bilgileri:")
            print(f"Server: {self.config['server']}")
            print(f"Database: {self.config['database']}")
            print(f"Username: {self.config['username']}")
            print("Bağlantı deneniyor...")
            
            self.connection = pyodbc.connect(self.connection_string)
            print("Bağlantı başarılı!")
            return True
            
        except Exception as e:
            print(f"MSSQL bağlantı hatası: {str(e)}")
            self.connection = None
            return False

    def disconnect(self) -> None:
        if self.connection:
            self.connection.close()
            self.connection = None

    def get_connection(self):
        """Havuzdan bağlantı al"""
        try:
            # Havuzda varsa
            while self.connection_pool:
                conn = self.connection_pool.pop()
                try:
                    # Test et
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    return conn
                except:
                    # Bağlantı kopmuşsa kapat
                    try:
                        conn.close()
                    except:
                        pass
                        
            # Yeni bağlantı aç
            if len(self.connection_pool) < self.max_pool_size:
                return pyodbc.connect(
                    self.connection_string,
                    timeout=self.connection_timeout
                )
                
            # Havuz doluysa bekle
            raise Exception("Bağlantı havuzu dolu!")
            
        except Exception as e:
            print(f"Bağlantı alma hatası: {str(e)}")
            return None

    def return_connection(self, conn):
        """Bağlantıyı havuza iade et"""
        try:
            if conn:
                if len(self.connection_pool) < self.max_pool_size:
                    self.connection_pool.append(conn)
                else:
                    conn.close()
        except:
            try:
                conn.close()
            except:
                pass

    def find_awb(self, awb: str) -> Dict[str, Any]:
        """MSSQL'de AWB ara"""
        conn = self.get_connection()
        try:
            print(f"Arama başladı MSSQL: {awb}")
            clean_awb = str(awb).strip()  # Input temizleme

            cursor = conn.cursor()
                
            base_query = self.config.get('table', '')
            if not base_query:
                print("SQL sorgusu bulunamadı!")
                return {}
                
            # ORDER BY'ı ayır
            order_by = ""
            base_parts = base_query.split("ORDER BY")
            if len(base_parts) > 1:
                base_query = base_parts[0]
                order_by = f" ORDER BY {base_parts[1]}"
                
            # TOP 1'i kaldır
            base_query = base_query.replace("SELECT top 1", "SELECT")
                
            searchable_columns = []
            column_mappings = self.full_config.get("datasource", {}).get("column_mappings", {})
                
            for col_name, details in column_mappings.items():
                if details.get("searchable", True):
                    searchable_columns.append(f"v.{col_name}")

            if not searchable_columns:
                search_column = self.full_config.get("datasource", {}).get("search_column")
                if search_column:
                    searchable_columns = [f"v.{search_column}"]

            if not searchable_columns:
                print("Aranabilir kolon bulunamadı!")
                return {}

            print(f"Aranabilir kolonlar: {searchable_columns}")

            # WHERE koşullarını oluştur
            where_conditions = " OR ".join([f"{col} LIKE ?" for col in searchable_columns])
                
            # Ana sorguyu oluştur - WHERE ve ORDER BY düzgün yerleştirildi
            base_query = base_query.rstrip(';')
            if 'WHERE' in base_query:
                query = f"{base_query} AND ({where_conditions}){order_by}"
            else:
                query = f"{base_query} WHERE {where_conditions}{order_by}"

            print("SQL Query:")
            print(query)
            print(f"Search params: {clean_awb}")

            # Sorguyu çalıştır
            search_params = [f"%{clean_awb}%" for _ in searchable_columns]
            cursor.execute(query, search_params)
                
            # İlk sonucu al
            row = cursor.fetchone()
                
            if row:
                columns = [column[0] for column in cursor.description]
                result = dict(zip(columns, row))
                    
                # Görünür kolonları filtrele
                visible_columns = {
                    col: details.get("display_name")
                    for col, details in column_mappings.items()
                    if details.get("visible", True)
                }
                    
                formatted_result = {
                    details: result.get(col, '')
                    for col, details in visible_columns.items()
                }
                print(f"Bulunan sonuç: {formatted_result}")
                return formatted_result
                    
            print("Sonuç bulunamadı")
            return {}
                
        except Exception as e:
            print(f"MSSQL arama hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}
        finally:
            self.return_connection(conn)

    def test_connection(self) -> bool:
        """Sadece bağlantıyı test et, tablo ve kolon kontrolü yapma"""
        try:
            # Temel bağlantı bilgilerini kontrol et
            if not all([
                self.config.get('server'),
                self.config.get('database'),
                self.config.get('username'),
                self.config.get('password')
            ]):
                print("HATA: Temel MSSQL ayarları eksik!")
                return False
            
            # Bağlantıyı test et
            conn = pyodbc.connect(self.connection_string)
            if conn:
                print("MSSQL bağlantısı başarılı!")
                conn.close()
                return True
            return False
            
        except Exception as e:
            print(f"MSSQL bağlantı hatası: {str(e)}")
            return False

    def _get_connection_string(self) -> str:
        """Bağlantı string'ini oluştur"""
        return self.connection_string

    def get_mssql_columns(self, table_name: str) -> List[str]:
        """Tablo kolonlarını getir"""
        try:
            # Bağlantı yoksa yeni bağlantı kur
            if not self.connection or self.connection.closed:
                if not self.connect():
                    raise Exception("Veritabanı bağlantısı kurulamadı!")

            cursor = self.connection.cursor()
            
            # Önce base query'den tablo adını al
            base_query = self.config.get('table', '')
            if not base_query:
                raise Exception("Tablo sorgusu bulunamadı!")

            # Kolon sorgusu
            query = """
                SELECT name 
                FROM sys.columns 
                WHERE object_id = OBJECT_ID(?)
            """
            
            print(f"Kolonlar sorgulanıyor için tablo: {table_name}")
            cursor.execute(query, [table_name])
            columns = [row[0] for row in cursor.fetchall()]
            
            print(f"Bulunan kolonlar: {columns}")
            return columns
            
        except Exception as e:
            print(f"Kolonları getirme hatası: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []
        finally:
            if self.connection:
                self.connection.close()
                self.connection = None

    def get_all_data(self) -> List[Dict[str, Any]]:
        """Tüm veriyi liste olarak döndür"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            query = self.config.get('table', '')
            if not query:
                return []
                
            cursor.execute(query)
            columns = [column[0] for column in cursor.description]
            
            results = []
            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Görünür kolonları filtrele
                visible_columns = {
                    col: details.get("display_name")
                    for col, details in self.full_config.get("datasource", {})
                                                         .get("column_mappings", {}).items()
                    if details.get("visible", True)
                }
                
                formatted_result = {
                    details: result.get(col, '')
                    for col, details in visible_columns.items()
                }
                results.append(formatted_result)
                
            return results
            
        except Exception as e:
            print(f"Veri alma hatası: {str(e)}")
            return []
        finally:
            self.return_connection(conn)

    def __del__(self):
        """Temizlik"""
        for conn in self.connection_pool:
            try:
                conn.close()
            except:
                pass
