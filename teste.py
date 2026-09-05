import collections
import random
import time


class WumpusWorld:

    def __init__(self, start=None, gold=None, wumpus=None, pits=None):
        self.grid_size = 4
        self.all_coords = [
            (r, c)
            for r in range(self.grid_size)
            for c in range(self.grid_size)
        ]

        self.setup_board(start, gold, wumpus, pits)

        # Estado do conhecimento lógico do Robô para cada célula
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
        r, c = cell
        adj = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                adj.append((nr, nc))
        return adj

    def read_sensors(self, cell):
        adj = self.get_adjacent(cell)
        breeze = any(neighbor in self.pits for neighbor in adj)
        stench = any(neighbor == self.wumpus_pos for neighbor in adj)
        glitter = cell == self.gold_pos
        return breeze, stench, glitter

    # -------------------------------------------------------------------------
    # ATUALIZAÇÃO E MOTOR DE DEDUÇÃO LÓGICA
    # -------------------------------------------------------------------------
    def update_knowledge(self, cell):
        self.visited.add(cell)
        self.pit_status[cell] = "NO"
        self.wumpus_status[cell] = "NO"

        breeze, stench, _ = self.read_sensors(cell)

        if breeze:
            self.breeze_sensed.add(cell)
        else:
            # Regra Direta: Sala visitada sem Brisa -> NENHUM vizinho tem poço
            for n in self.get_adjacent(cell):
                self.pit_status[n] = "NO"

        if stench:
            self.stench_sensed.add(cell)
        else:
            # Regra Direta: Sala visitada sem Fedor -> NENHUM vizinho é Wumpus
            for n in self.get_adjacent(cell):
                self.wumpus_status[n] = "NO"

        # Aplica o motor inferencial completo até convergir
        self._apply_deductions()

    def _apply_deductions(self):
        changed = True
        while changed:
            changed = False

            # --- 1. DEDUÇÃO DO WUMPUS ---
            wumpus_confirmed_cell = None
            for cell in self.all_coords:
                if self.wumpus_status[cell] == "CONFIRMED":
                    wumpus_confirmed_cell = cell
                    break

            if wumpus_confirmed_cell:
                # Wumpus localizado: descarta Wumpus em todas as outras salas
                for cell in self.all_coords:
                    if (
                        cell != wumpus_confirmed_cell
                        and self.wumpus_status[cell] != "NO"
                    ):
                        self.wumpus_status[cell] = "NO"
                        changed = True
            elif self.stench_sensed:
                # Interseção de salas com Fedor
                possible_wumpus = set(self.all_coords)
                for s_cell in self.stench_sensed:
                    adj_candidates = {
                        n
                        for n in self.get_adjacent(s_cell)
                        if self.wumpus_status[n] != "NO"
                    }
                    possible_wumpus &= adj_candidates

                if len(possible_wumpus) == 1:
                    w_cell = list(possible_wumpus)[0]
                    if self.wumpus_status[w_cell] != "CONFIRMED":
                        self.wumpus_status[w_cell] = "CONFIRMED"
                        changed = True

            # --- 2. DEDUÇÃO DE POÇOS (Candidato Único por Brisa) ---
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

            # --- 2.1 REGRA DA CONTAGEM TOTAL DE POÇOS ---
            confirmed_pits = [
                c for c in self.all_coords if self.pit_status[c] == "CONFIRMED"
            ]
            if len(confirmed_pits) == 2:
                for c in self.all_coords:
                    if self.pit_status[c] == "POSSIBLE":
                        self.pit_status[c] = "NO"
                        changed = True

            # --- 3. ELIMINAÇÃO DE SUSPEITAS DE POÇO (Brisas Explicadas) ---
            for cell in self.all_coords:
                if (
                    cell not in self.visited
                    and self.pit_status[cell] == "POSSIBLE"
                ):
                    visited_adj = [
                        n for n in self.get_adjacent(cell) if n in self.visited
                    ]

                    if not visited_adj:
                        continue

                    is_needed_for_pit = False
                    for adj_visited in visited_adj:
                        if adj_visited in self.breeze_sensed:
                            has_confirmed_pit = any(
                                self.pit_status[n] == "CONFIRMED"
                                for n in self.get_adjacent(adj_visited)
                            )
                            if not has_confirmed_pit:
                                is_needed_for_pit = True
                                break

                    if not is_needed_for_pit:
                        self.pit_status[cell] = "NO"
                        changed = True

            # --- 4. ELIMINAÇÃO DE SUSPEITAS DE WUMPUS (Fedores Explicados) ---
            for cell in self.all_coords:
                if (
                    cell not in self.visited
                    and self.wumpus_status[cell] == "POSSIBLE"
                ):
                    visited_adj = [
                        n for n in self.get_adjacent(cell) if n in self.visited
                    ]

                    if not visited_adj:
                        continue

                    is_needed_for_wumpus = False
                    for adj_visited in visited_adj:
                        if adj_visited in self.stench_sensed:
                            has_confirmed_wumpus = any(
                                self.wumpus_status[n] == "CONFIRMED"
                                for n in self.get_adjacent(adj_visited)
                            )
                            if not has_confirmed_wumpus:
                                is_needed_for_wumpus = True
                                break

                    if not is_needed_for_wumpus:
                        self.wumpus_status[cell] = "NO"
                        changed = True

    # -------------------------------------------------------------------------
    # NAVEGAÇÃO SEGURA (BFS)
    # -------------------------------------------------------------------------
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

    # -------------------------------------------------------------------------
    # RENDERIZAÇÃO NO TERMINAL
    # -------------------------------------------------------------------------
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

        if not p_possible and not w_possible and visited_adj:
            return "🟢"
        if p_possible and w_possible and visited_adj:
            return "🌐"
        if p_possible and visited_adj:
            return "🔵"
        if w_possible and visited_adj:
            return "🟡"

        return "⬛"

    def render_grid(self, action_msg=""):
        breeze, stench, glitter = self.read_sensors(self.current_pos)

        print("\n" + "=" * 55)
        print(f"🐾 PASSO {self.step_counter} | 🎬 AÇÃO: {action_msg}")
        print("=" * 55)

        print(f"📍 Posição Atual do Robô: {self.current_pos}")

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

        # --- NOVOS CAMPOS EXIBINDO SUSPEITAS DE PERIGO ---
        possible_pits = [
            c for c in self.all_coords
            if self.pit_status[c] == "POSSIBLE" and c not in self.visited
        ]
        possible_wumpus = [
            c for c in self.all_coords
            if self.wumpus_status[c] == "POSSIBLE" and c not in self.visited
        ]

        p_str = possible_pits if possible_pits else "Nenhum"
        w_str = possible_wumpus if possible_wumpus else "Nenhum"

        print(f"⚠️  Casas de Possíveis Poços (?P): {p_str}")
        print(f"⚠️  Casas de Possível Wumpus (?W): {w_str}")

        print("-" * 55)

        print("      c0  c1  c2  c3")
        print("    +-----------------+")
        for r in range(self.grid_size - 1, -1, -1):
            row_str = f" r{r} | "
            for c in range(self.grid_size):
                cell_repr = self.get_cell_symbol((r, c))
                row_str += f"{cell_repr}  "
            print(row_str + "|")
        print("    +-----------------+")
        print(
            "Legenda: 🤖 Robô | 🟩 Visitado | 🟢 Seguro | 🟡 ?W | 🔵 ?P | 🌐 ?WP | 🦨 Wumpus | 🛑 Poço | 💰 Ouro"
        )
        print("-" * 55)

    # -------------------------------------------------------------------------
    # EXECUÇÃO DA SIMULAÇÃO
    # -------------------------------------------------------------------------
    def solve(self):
        print("\n" + "⚙️ " * 15)
        print("  GABARITO INICIAL DA CAVERNA (POSIÇÕES REAIS)")
        print("⚙️ " * 15)
        print(f"  🤖 Robô (Início): {self.start_pos}")
        print(f"  💰 Ouro:          {self.gold_pos}")
        print(f"  🦨 Wumpus:        {self.wumpus_pos}")
        print(f"  🛑 Poços:         {list(self.pits)}")
        print("⚙️ " * 15 + "\n")

        time.sleep(1)
        self.render_grid(
            action_msg=f"Robô colocado na posição inicial {self.start_pos}"
        )

        while True:
            self.update_knowledge(self.current_pos)

            _, _, glitter = self.read_sensors(self.current_pos)
            if glitter:
                print(
                    "\n🏆 VITÓRIA! O Pote de Ouro foi encontrado com sucesso!"
                )
                print("🏁 CAMINHO SEGURO PERCORRIDO ATÉ O OURO:")
                print(" -> ".join(f"[{r},{c}]" for r, c in self.path_taken))
                return True

            # Salas 100% seguras que ainda não foram visitadas
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
                print(" -> ".join(f"[{r},{c}]" for r, c in self.path_taken))
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
                print(" -> ".join(f"[{r},{c}]" for r, c in self.path_taken))
                break

            proximo_passo = melhor_rota[1]
            self.current_pos = proximo_passo
            self.path_taken.append(proximo_passo)
            self.step_counter += 1

            time.sleep(0.8)
            self.render_grid(
                action_msg=f"Movimentou-se para a sala {proximo_passo}"
            )


# -----------------------------------------------------------------------------
# ENTRADA DE DADOS
# -----------------------------------------------------------------------------
def get_coordinate_input(prompt):
    val = input(prompt).strip()
    if not val:
        return None
    try:
        r, c = map(int, val.split(","))
        if 0 <= r < 4 and 0 <= c < 4:
            return (r, c)
    except ValueError:
        pass
    print("⚠️ Entrada inválida. Sorteando posição aleatória...")
    return None


if __name__ == "__main__":
    print("=" * 55)
    print("      DESAFIO DO LABIRINTO WUMPUS 4x4 (AGENTE LÓGICO)")
    print("=" * 55)
    print("💡 DICA: Pressione [ENTER] para sortear qualquer coordenada aleatoriamente.\n")

    start_in = get_coordinate_input("👉 Posição Inicial do Robô (linha,coluna): ")
    gold_in = get_coordinate_input("👉 Posição do Ouro (linha,coluna): ")
    wumpus_in = get_coordinate_input("👉 Posição do Wumpus (linha,coluna): ")

    pits_in = []
    p1 = get_coordinate_input("👉 Posição do Poço 1 (linha,coluna): ")
    if p1:
        pits_in.append(p1)
    p2 = get_coordinate_input("👉 Posição do Poço 2 (linha,coluna): ")
    if p2:
        pits_in.append(p2)

    game = WumpusWorld(
        start=start_in, gold=gold_in, wumpus=wumpus_in, pits=pits_in
    )
    game.solve()