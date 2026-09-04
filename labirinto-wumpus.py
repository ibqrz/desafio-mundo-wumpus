## Labirinto Wumpus

import collections
import random

GRID_SIZE = 4

class WumpusWorld:
    def __init__(self, start=(0,0), golsd=(2,2), wumpus=(0,2), pits=[(2,0), (3,3)]):
        self.start = start
        self.gold = gold
        self.wumpus = wumpus
        self.pits = pits
        
        # Estruturas do Agente IA
        self.visited = set([start])
        self.safe_rooms = set([start])
        self.dangerous_rooms = {} # (x,y) -> "Wumpus" | "Poço" | "Perigo"
        self.suspect_pits = set()
        self.suspect_wumpus = set()
        self.path_history = [start]
        self.current_pos = start
        self.found_gold = False

    def is_valid(self, x, y):
        return 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE

    def get_adjacent(self, x, y):
        adj = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = x + dx, y + dy
            if self.is_valid(nx, ny):
                adj.append((nx, ny))
        return adj

    def read_sensors(self, x, y):
        """Retorna os sensores (breeze, stench, glitter) na sala (x,y)."""
        breeze = False
        stench = False
        glitter = ((x, y) == self.gold)

        for nx, ny in self.get_adjacent(x, y):
            if (nx, ny) == self.wumpus:
                stench = True
            if (nx, ny) in self.pits:
                breeze = True

        return breeze, stench, glitter

    def deduce_dangers(self):
        """Aplica dedução lógica proposicional básica nos sensores percebidos."""
        for vx, vy in list(self.visited):
            breeze, stench, _ = self.read_sensors(vx, vy)
            adj = self.get_adjacent(vx, vy)
            unvisited_unknowns = [p for p in adj if p not in self.safe_rooms and p not in self.visited]

            if stench and len(unvisited_unknowns) == 1:
                target = unvisited_unknowns[0]
                if target not in self.dangerous_rooms:
                    self.dangerous_rooms[target] = "Wumpus"

            if breeze and len(unvisited_unknowns) == 1:
                target = unvisited_unknowns[0]
                if target not in self.dangerous_rooms:
                    self.dangerous_rooms[target] = "Poço"

    def find_nearest_unvisited_safe(self):
        """BFS para encontrar o caminho seguro mais curto até uma sala segura não visitada."""
        queue = collections.deque([[self.current_pos]])
        visited_bfs = {self.current_pos}

        while queue:
            path = queue.popleft()
            cx, cy = path[-1]

            if (cx, cy) in self.safe_rooms and (cx, cy) not in self.visited:
                return path

            for nx, ny in self.get_adjacent(cx, cy):
                if (nx, ny) in self.safe_rooms and (nx, ny) not in visited_bfs:
                    visited_bfs.add((nx, ny))
                    queue.append(path + [(nx, ny)])
        return None

    def print_board(self):
        """Imprime no terminal a visualização gráfica do tabuleiro 4x4 em Emojis."""
        print("\n" + "="*35)
        print(f" MAPA DO MUNDO WUMPUS (4x4) - Pos Atual: {self.current_pos}")
        print("="*35)
        
        # Y varia de 3 até 0 (visualização cartesiana padrão)
        for y in range(GRID_SIZE - 1, -1, -1):
            row_str = f"{y} | "
            for x in range(GRID_SIZE):
                pos = (x, y)
                if pos == self.current_pos:
                    cell = "🤖" # Robô
                elif pos == self.gold and pos in self.visited:
                    cell = "💰" # Ouro encontrado
                elif pos in self.dangerous_rooms:
                    cell = "🛑" # Perigo confirmado
                elif pos in self.visited:
                    b, s, _ = self.read_sensors(x, y)
                    icons = ""
                    if b: icons += "💨"
                    if s: icons += "🦨"
                    cell = icons if icons else "⬜"
                elif pos in self.safe_rooms:
                    cell = "🟩" # Confirmado seguro
                elif pos in self.suspect_pits or pos in self.suspect_wumpus:
                    cell = "❓" # Suspeito
                else:
                    cell = "⬛" # Inexplorado

                row_str += f"{cell:^4}"
            print(row_str)
        print("    " + "-"*16)
        print("     0   1   2   3 (X)\n")

    def run_exploration(self):
        """Executa o loop de raciocínio autônomo do agente de IA."""
        step = 0
        while True:
            step += 1
            cx, cy = self.current_pos
            breeze, stench, glitter = self.read_sensors(cx, cy)

            sensor_list = []
            if glitter: sensor_list.append("BRILHO ✨")
            if breeze: sensor_list.append("BRISA 💨")
            if stench: sensor_list.append("FEDOR 🦨")
            if not sensor_list: sensor_list.append("NENHUM")

            print(f"--- PASSO {step} ---")
            print(f"📍 Robô em ({cx}, {cy}) | Sensores: {', '.join(sensor_list)}")

            # Condição de Sucesso
            if glitter:
                self.found_gold = True
                self.print_board()
                print("🎉 SUCESSO! O ouro foi encontrado seguro!")
                print(f"🏆 Caminho seguro percorrido: {self.path_history}")
                return True

            # Atualização dos Sensores & Inferência
            adj = self.get_adjacent(cx, cy)
            if not breeze and not stench:
                for nxt in adj:
                    if nxt not in self.dangerous_rooms:
                        self.safe_rooms.add(nxt)
            else:
                for nxt in adj:
                    if nxt not in self.visited and nxt not in self.safe_rooms:
                        if breeze: self.suspect_pits.add(nxt)
                        if stench: self.suspect_wumpus.add(nxt)

            self.deduce_dangers()
            self.print_board()

            # Escolha do Próximo Passo
            unvisited_safe = [p for p in adj if p in self.safe_rooms and p not in self.visited]
            
            if unvisited_safe:
                self.current_pos = unvisited_safe[0]
                self.visited.add(self.current_pos)
                self.path_history.append(self.current_pos)
            else:
                path = self.find_nearest_unvisited_safe()
                if path and len(path) > 1:
                    next_step = path[1]
                    print(f"↩️ Recuando até a próxima sala segura em {path[-1]} (Próximo: {next_step})")
                    self.current_pos = next_step
                    self.visited.add(next_step)
                    self.path_history.append(next_step)
                else:
                    print("❌ NÃO HÁ CAMINHO SEGURO CONFIRMADO ATÉ O OURO!")
                    print(f"Caminho seguro percorrido até o momento: {self.path_history}")
                    return False


# --- ENTRADA DE DADOS & LOOP PRINCIPAL ---
if __name__ == "__main__":
    print("==========================================")
    print("   DESAFIO DO LABIRINTO WUMPUS 4x4 (IA)   ")
    print("==========================================")
    
    opcao = input("Deseja inserir posições customizadas? (s/n, padrão=n): ").strip().lower()
    
    if opcao == 's':
        def parse_pos(prompt):
            x, y = map(int, input(prompt).split(','))
            return (x, y)

        start = parse_pos("Posição inicial do Robô (X,Y): ")
        gold = parse_pos("Posição do Ouro (X,Y): ")
        wumpus = parse_pos("Posição do Wumpus (X,Y): ")
        p1 = parse_pos("Posição do Poço 1 (X,Y): ")
        p2 = parse_pos("Posição do Poço 2 (X,Y): ")
        pits = [p1, p2]
    else:
        # Padrão
        start = (0, 0)
        gold = (2, 2)
        wumpus = (0, 2)
        pits = [(2, 0), (3, 3)]
        print(f"Usando padrão: Robô={start}, Ouro={gold}, Wumpus={wumpus}, Poços={pits}")

    world = WumpusWorld(start=start, gold=gold, wumpus=wumpus, pits=pits)
    world.run_exploration()