import threading
import time

# Eine Liste zum Speichern der verbundenen Server
connected_servers = []

# Mutex für kritische Abschnitte
mutex = threading.Lock()

# Funktion zum Überwachen der Server und Aktualisieren der Serverliste
def monitor_servers():
    global connected_servers
    global mutex

    while True:
        # Überwachungslogik hier einfügen, um die Verfügbarkeit der Server zu prüfen
        # Beispiel: Ping oder Socket-Verbindung überprüfen

        # Aktualisiere die Liste der verbundenen Server
        with mutex:
            connected_servers = [("localhost", 12345), ("localhost", 12346)]  # Beispielwerte

        # Wartezeit zwischen den Aktualisierungen
        time.sleep(10)

# Funktion zum Abrufen des aktuellen aktiven Servers
def get_active_server():
    global connected_servers
    global mutex

    with mutex:
        return connected_servers[0] if connected_servers else ("localhost", 12345)  # Fallback auf lokale Adresse

# Starte den Server-Management-Thread
def start_server_manager():
    server_manager_thread = threading.Thread(target=monitor_servers)
    server_manager_thread.start()

if __name__ == "__main__":
    start_server_manager()
