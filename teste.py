import collections
import itertools
import random
import time


class WumpusWorld:

    def __init__(self, start=None, gold=None, wumpus=None, pits=None):
        self.grid_size = 4
        # Coordenadas tratadas como (X, Y) -> (Coluna, Linha)
        self.all_coords = [
            (x, y)
            for x in range(self.grid_size)
            for y in range(self.grid_size)
        ]

        self.setup_board(start, gold, wumpus, pits)

        # Status de Poço: 'CONFIRMED', 'POSSIBLE', 'NO'
        self.pit_status = {cell: "POSSIBLE" for cell in self.all_coords}
        # Status de Wumpus: 'CONFIRMED', 'POSSIBLE', 'NO'
        self.wumpus_status = {cell: "POSSIBLE" for cell in self.all_coords}

        self.visited = set()
        self.breeze_sensed = set()
        self.stench_sensed = set()

        self.current_pos = self.start_pos
        self.path_taken = [self.start_pos]
        self.step_counter = 0

        # Posição inicial é garantidamente segura
        self.pit_status[self.start_pos] = "NO"
        self.wumpus_status[self.start_pos] = "NO"

    def setup_board(self, start, gold, wumpus, pits):
        if start is None:
            self.start_pos = (random.randint(0, 3), random.randint(0, 3))
        else:
            self.start_pos = tuple(start)

        available = [c for c in self.all_coords if c != self.start_pos]

        if gold is None:
            self.gold_pos = random.choice(available)
        else:
            self.gold_pos = tuple(gold)

        available = [c for c in available if c != self.gold_pos]

        if wumpus is None:
            self.wumpus_pos = random.choice(available)
        else:
            self.wumpus_pos = tuple(wumpus)

        if pits is None or len(pits) < 2:
            pit_candidates = [c for c in available if c != self.wumpus_pos]
            self.pits = set(random.sample(pit_candidates, 2))
        else:
            self.pits = set(tuple(p) for p in pits[:2])

    def get_adjacent(self, cell):
        x, y = cell
        adj = []
        # Deslocamentos em (dX, dY)
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                adj.append((nx, ny))
        return adj

    def read_sensors(self, cell):
        adj = self.get_adjacent(cell)
        breeze = any(neighbor in self.pits for neighbor in adj)
        stench = any(neighbor == self.wumpus_pos for neighbor in adj)
        glitter = cell == self.gold_pos
        return breeze, stench, glitter

    def update_knowledge(self, cell):
        self.visited.add(cell)
        self.pit_status[cell] = "NO"
        self.wumpus_status[cell] = "NO"

        breeze, stench, _ = self.read_sensors(cell)

        if breeze:
            self.breeze_sensed.add(cell)
        else:
            for n in self.get_adjacent(cell):
                self.pit_status[n] = "NO"

        if stench:
            self.stench_sensed.add(cell)
        else:
            for n in self.get_adjacent(cell):
                self.wumpus_status[n] = "NO"

        self._apply_deductions()

    def _apply_deductions(self):
        changed = True
        while changed:
            changed = False

            # --- 1. DEDUÇÃO DO WUMPUS ---
            if self.stench_sensed:
                wumpus_confirmed_cell = None
                for cell in self.all_coords:
                    if self.wumpus_status[cell] == "CONFIRMED":
                        wumpus_confirmed_cell = cell
                        break

                if wumpus_confirmed_cell:
                    for cell in self.all_coords:
                        if (
                            cell != wumpus_confirmed_cell
                            and self.wumpus_status[cell] != "NO"
                        ):
                            self.wumpus_status[cell] = "NO"
                            changed = True
                else:
                    possible_wumpus = set(self.all_coords)
                    for s_cell in self.stench_sensed:
                        adj_candidates = {
                            n
                            for n in self.get_adjacent(s_cell)
                            if self.wumpus_status[n] != "NO"
                        }
                        possible_wumpus &= adj_candidates

                    for cell in self.all_coords:
                        if (
                            cell not in possible_wumpus
                            and self.wumpus_status[cell] != "NO"
                        ):
                            self.wumpus_status[cell] = "NO"
                            changed = True

                    if len(possible_wumpus) == 1:
                        w_cell = list(possible_wumpus)[0]
                        if self.wumpus_status[w_cell] != "CONFIRMED":
                            self.wumpus_status[w_cell] = "CONFIRMED"
                            changed = True

            # --- 2. DEDUÇÃO DE POÇOS (Candidato Único) ---
            for b_cell in self.breeze_sensed:
                candidates = [
                    n
                    for n in self.get_adjacent(b_cell)
                    if self.pit_status[n] in ("POSSIBLE", "CONFIRMED")
                ]
                if len(candidates) == 1:
                    p_cell = candidates[0]
                    if self.pit_status[p_cell] != "CONFIRMED":
                        self.pit_status[p_cell] = "CONFIRMED"
                        changed = True

            # --- 3. LIMITE DE POÇOS (Máximo 2 Poços) ---
            confirmed_pits = {
                c for c in self.all_coords if self.pit_status[c] == "CONFIRMED"
            }
            if len(confirmed_pits) == 2:
                for c in self.all_coords:
                    if self.pit_status[c] == "POSSIBLE":
                        self.pit_status[c] = "NO"
                        changed = True

            # --- 4. HIPÓTESE E SATISFIABILIDADE DE POÇOS ---
            possible_pits = [
                cell
                for cell in self.all_coords
                if self.pit_status[cell] == "POSSIBLE"
            ]
            max_pits = 2

            if self.breeze_sensed and possible_pits:
                for c in list(possible_pits):
                    rem_budget = max_pits - len(confirmed_pits) - 1

                    if rem_budget < 0:
                        self.pit_status[c] = "NO"
                        changed = True
                        continue

                    other_candidates = [p for p in possible_pits if p != c]
                    is_c_valid = False

                    for r in range(
                        min(rem_budget + 1, len(other_candidates) + 1)
                    ):
                        for extra in itertools.combinations(
                            other_candidates, r
                        ):
                            hypo_pits = confirmed_pits | {c} | set(extra)

                            all_breezes_covered = True
                            for b_cell in self.breeze_sensed:
                                adj = set(self.get_adjacent(b_cell))
                                if not (adj & hypo_pits):
                                    all_breezes_covered = False
                                    break

                            if all_breezes_covered:
                                is_c_valid = True
                                break
                        if is_c_valid:
                            break

                    if not is_c_valid:
                        self.pit_status[c] = "NO"
                        changed = True

    def rota_segura_bfs(self, pos_inicial, pos_objetivo):
        queue = collections.deque([[pos_inicial]])
        seen = {pos_inicial}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            if curr == pos_objetivo:
                return path

            for n in self.get_adjacent(curr):
                is_navigable = n in self.visited or (
                    self.pit_status[n] == "NO" and self.wumpus_status[n] == "NO"
                )
                if is_navigable and n not in seen:
                    seen.add(n)
                    queue.append(path + [n])
        return None

    def get_cell_symbol(self, cell):
        if cell == self.current_pos:
            return "🤖"
        if cell == self.gold_pos and cell in self.visited:
            return "💰"
        if self.pit_status[cell] == "CONFIRMED":
            return "🛑"
        if self.wumpus_status[cell] == "CONFIRMED":
            return "🦨"
        if cell in self.visited:
            return "🟩"

        p_possible = self.pit_status[cell] == "POSSIBLE"
        w_possible = self.wumpus_status[cell] == "POSSIBLE"
        visited_adj = any(n in self.visited for n in self.get_adjacent(cell))

        if visited_adj:
            if not p_possible and not w_possible:
                return "🟢"
            if p_possible and w_possible:
                return "🌐"
            if p_possible:
                return "🔵"
            if w_possible:
                return "🟡"

        return "⬛"

    def render_grid(self, action_msg=""):
        breeze, stench, glitter = self.read_sensors(self.current_pos)

        print("\n" + "=" * 55)
        print(f"🐾 PASSO {self.step_counter} | 🎬 AÇÃO: {action_msg}")
        print("=" * 55)

        print(f"📍 Posição Atual do Robô (X, Y): {self.current_pos}")

        sensores_ativos = []
        if breeze:
            sensores_ativos.append("🍃 Brisa")
        if stench:
            sensores_ativos.append("🤢 Fedor")
        if glitter:
            sensores_ativos.append("✨ Brilho")

        sensor_str = (
            ", ".join(sensores_ativos) if sensores_ativos else "Nenhum (Limpo)"
        )
        print(f"📡 Sensores no local: {sensor_str}")

        b_list = list(self.breeze_sensed) if self.breeze_sensed else "Nenhum"
        s_list = list(self.stench_sensed) if self.stench_sensed else "Nenhum"
        print(f"🗺️  Histórico de Locais com Brisa: {b_list}")
        print(f"🗺️  Histórico de Locais com Fedor: {s_list}")

        print("-" * 55)

        # Desenha a grade: Linhas (Y) do topo (3) para a base (0), Colunas (X) da esq (0) para dir (3)
        print("      c0  c1  c2  c3")
        print("    +-----------------+")
        for y in range(self.grid_size - 1, -1, -1):
            row_str = f" r{y} | "
            for x in range(self.grid_size):
                cell_repr = self.get_cell_symbol((x, y))
                row_str += f"{cell_repr}  "
            print(row_str + "|")
        print("    +-----------------+")
        print(
            "Legenda: 🤖 Robô | 🟩 Visitado | 🟢 Seguro | 🟡 ?W | 🔵 ?P | 🌐 ?WP | 🦨 Wumpus | 🛑 Poço | 💰 Ouro"
        )
        print("-" * 55)

    def solve(self):
        print("\n" + "⚙️ " * 15)
        print("  GABARITO INICIAL DA CAVERNA (POSIÇÕES REAIS em X,Y)")
        print("⚙️ " * 15)
        print(f"  🤖 Robô (Início): {self.start_pos}")
        print(f"  💰 Ouro:          {self.gold_pos}")
        print(f"  🦨 Wumpus:        {self.wumpus_pos}")
        print(f"  🛑 Poços:         {list(self.pits)}")
        print("⚙️ " * 15 + "\n")

        self.update_knowledge(self.current_pos)

        time.sleep(1)
        self.render_grid(
            action_msg=f"Robô colocado na posição inicial {self.start_pos}"
        )

        while True:
            _, _, glitter = self.read_sensors(self.current_pos)
            if glitter:
                print(
                    "\n🏆 VITÓRIA! O Pote de Ouro foi encontrado com sucesso!"
                )
                print("🏁 CAMINHO SEGURO PERCORRIDO ATÉ O OURO (X, Y):")
                print(" -> ".join(f"[{x},{y}]" for x, y in self.path_taken))
                return True

            objetivos = [
                c
                for c in self.all_coords
                if c not in self.visited
                and self.pit_status[c] == "NO"
                and self.wumpus_status[c] == "NO"
            ]

            if not objetivos:
                print("\n❌ NÃO HÁ CAMINHO SEGURO CONFIRMADO ATÉ O OURO!")
                print(
                    "A IA interrompeu a movimentação para evitar riscos de falha/morte."
                )
                print("\n📍 CAMINHO SEGURO PERCORRIDO ATÉ O MOMENTO DA PARADA:")
                print(" -> ".join(f"[{x},{y}]" for x, y in self.path_taken))
                break

            melhor_rota = None
            for obj in objetivos:
                rota = self.rota_segura_bfs(self.current_pos, obj)
                if rota:
                    if melhor_rota is None or len(rota) < len(melhor_rota):
                        melhor_rota = rota

            if not melhor_rota or len(melhor_rota) < 2:
                print("\n❌ Não foi possível traçar uma rota segura.")
                print("\n📍 CAMINHO SEGURO PERCORRIDO ATÉ O MOMENTO DA PARADA:")
                print(" -> ".join(f"[{x},{y}]" for x, y in self.path_taken))
                break

            proximo_passo = melhor_rota[1]
            self.current_pos = proximo_passo
            self.path_taken.append(proximo_passo)
            self.step_counter += 1

            self.update_knowledge(self.current_pos)

            time.sleep(0.8)
            self.render_grid(
                action_msg=f"Movimentou-se para a sala {proximo_passo}"
            )


def get_coordinate_input(prompt):
    val = input(prompt).strip()
    if not val:
        return None
    try:
        x, y = map(int, val.split(","))
        if 0 <= x < 4 and 0 <= y < 4:
            return (x, y)
    except ValueError:
        pass
    print("⚠️ Entrada inválida. Sorteando posição aleatória...")
    return None


if __name__ == "__main__":
    print("=" * 55)
    print("      DESAFIO DO LABIRINTO WUMPUS 4x4 (AGENTE LÓGICO)")
    print("=" * 55)
    print(
        "💡 FORMATO DE ENTRADA: X,Y  (Onde X = Coluna [0-3] e Y = Linha [0-3])"
    )
    print("💡 Pressione [ENTER] para sortear qualquer posição aleatoriamente.\n")

    start_in = get_coordinate_input(
        "👉 Posição Inicial do Robô (Coluna X, Linha Y): "
    )
    gold_in = get_coordinate_input(
        "👉 Posição do Ouro (Coluna X, Linha Y): "
    )
    wumpus_in = get_coordinate_input(
        "👉 Posição do Wumpus (Coluna X, Linha Y): "
    )

    pits_in = []
    p1 = get_coordinate_input("👉 Posição do Poço 1 (Coluna X, Linha Y): ")
    if p1:
        pits_in.append(p1)
    p2 = get_coordinate_input("👉 Posição do Poço 2 (Coluna X, Linha Y): ")
    if p2:
        pits_in.append(p2)

    game = WumpusWorld(
        start=start_in, gold=gold_in, wumpus=wumpus_in, pits=pits_in
    )
    game.solve()