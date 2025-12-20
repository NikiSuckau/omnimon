import struct
import random

try:
    from battle_utils import get_attack_pattern
    from battle_utils import get_dm20_attack_pattern
    from models import *
except ImportError:
    # Absolute imports for direct testing
    from core.combat.sim.battle_utils import get_attack_pattern
    from core.combat.sim.battle_utils import get_dm20_attack_pattern
    from core.combat.sim.models import *


class BattleSimulator:
    def __init__(self, protocol: BattleProtocol):
        self.protocol = protocol

    def simulate(self, device1: Digimon, device2: Digimon) -> BattleResult:
        if self.protocol == BattleProtocol.DMC_BS:
            result = self._simulate_dmc_bs(device1, device2)
        elif self.protocol == BattleProtocol.DM20_BS:
            result = self._simulate_dm20_bs(device1, device2)
        elif self.protocol == BattleProtocol.DMX_BS:
            result = self._simulate_dmx_bs(device1, device2)
        elif self.protocol == BattleProtocol.PEN20_BS:
            result = self._simulate_pen20_bs(device1, device2)
        else:
            raise NotImplementedError("Protocol not implemented")
        
        self.print_battle_log(result)
        return result
    
    def print_battle_log(self, result):
        # Generate a detailed battle log
        print(f"Winner: {result.winner}")

        # Print final states of both devices
        print("Device 1:")
        for i, status in enumerate(result.device1_final):
            print(f"  {i}: {status.name} (HP: {status.hp}, Alive: {status.alive})")
        print("Device 2:")
        for i, status in enumerate(result.device2_final):
            print(f"  {i}: {status.name} (HP: {status.hp}, Alive: {status.alive})")
        print()

        # Iterate through the battle log
        for turn_data in result.battle_log:
            print(f"Turn {turn_data.turn}")

            # Device 1 attacks
            print(" Device 1 attacks:")
            for attack in turn_data.attacks:
                if attack.device == "device1":
                    attacker_name = result.device1_final[attack.attacker].name
                    defender_name = result.device2_final[attack.defender].name if attack.defender >= 0 else "?"
                    print(f"   {attacker_name} -> {defender_name}: hit={attack.hit} dmg={attack.damage}")

            # Device 2 attacks
            print(" Device 2 attacks:")
            for attack in turn_data.attacks:
                if attack.device == "device2":
                    attacker_name = result.device2_final[attack.attacker].name
                    defender_name = result.device1_final[attack.defender].name if attack.defender >= 0 else "?"
                    print(f"   {attacker_name} -> {defender_name}: hit={attack.hit} dmg={attack.damage}")

            # Print status of both devices
            device1_status = [f"{status.name}({status.hp})" for status in turn_data.device1_status]
            device2_status = [f"{status.name}({status.hp})" for status in turn_data.device2_status]
            print(f" Device 1 status: {device1_status}")
            print(f" Device 2 status: {device2_status}")
            print()

        # Print exchanged packet data
        print("Exchanged Packet Data:")
        print("Device 1 Packets:")
        for i, packet in enumerate(result.device1_packets):
            self._print_packet(i, packet)

        print("Device 2 Packets:")
        for i, packet in enumerate(result.device2_packets):
            self._print_packet(i, packet)

    def _print_packet(self, index, packet):
        """
        Helper method to print a single packet in binary and hexadecimal formats.
        Handles different packet formats (bytes, list of bytes, etc.).
        """
        if isinstance(packet, bytes):
            # Process raw bytes
            binary = " ".join(f"{byte:08b}" for byte in packet)
            hex_representation = " ".join(f"{byte:02X}" for byte in packet)
            print(f"  Packet {index + 1}:")
            print(f"    Binary: {binary}")
            print(f"    Hex: {hex_representation}")
        elif isinstance(packet, list):
            # Concatenate list of bytes into a single bytes object
            concatenated = b"".join(packet)
            binary = " ".join(f"{byte:08b}" for byte in concatenated)
            hex_representation = " ".join(f"{byte:02X}" for byte in concatenated)
            print(f"  Packet {index + 1}:")
            print(f"    Binary: {binary}")
            print(f"    Hex: {hex_representation}")
        else:
            # Handle invalid packet types
            print(f"  Packet {index + 1}: Invalid packet type: {type(packet)}")

    def _simulate_dmc_bs(self, attacker: Digimon, defender: Digimon) -> BattleResult:
        """
        Simulates a battle using the DMC protocol.
        :param attacker: The attacking Digimon (device1).
        :param defender: The defending Digimon (device2).
        :return: A BattleResult object.
        """
        dev_att = DMCDevice(attacker)
        dev_def = DMCDevice(defender)

        # Initialize packet storage
        device1_packets = []
        device2_packets = []

        # Step 1: Device 1 sends Packet 1 (operation 0)
        att_packet1 = dev_att.generate_packet1(operation=0)
        dev_def.process_packet(att_packet1)
        device1_packets.append(att_packet1)

        # Step 2: Device 2 responds with Packet 1 (operation 1)
        def_packet1 = dev_def.generate_packet1(operation=1)
        dev_att.process_packet(def_packet1)
        device2_packets.append(def_packet1)

        # Step 3: Calculate the outcome
        outcome_device1 = dev_att.calculate_outcome(dev_def)
        outcome_device2 = 1 - outcome_device1  # Opposite outcome

        # Step 4: Device 1 sends Packet 2 (operation 2)
        att_packet2 = dev_att.generate_packet2(operation=2, outcome=outcome_device1)
        dev_def.process_packet(att_packet2)
        device1_packets.append(att_packet2)

        # Step 5: Device 2 responds with Packet 2 (operation 3)
        def_packet2 = dev_def.generate_packet2(operation=3, outcome=outcome_device2)
        dev_att.process_packet(def_packet2)
        device2_packets.append(def_packet2)

        # Step 6: Simulate the battle using attack patterns
        attacker_hp = dev_att.hp
        defender_hp = dev_def.hp
        battle_log = []

        # Determine winner and loser
        if outcome_device1 == 1:
            winner_device = dev_att
            loser_device = dev_def
            winner_pattern = get_attack_pattern(attacker.level, attacker.mini_game, protocol="DMC_WINNER")
            loser_pattern = get_attack_pattern(defender.level, defender.mini_game, protocol="DMC_LOOSER")
            winner_name = attacker.name
            loser_name = defender.name
        else:
            winner_device = dev_def
            loser_device = dev_att
            winner_pattern = get_attack_pattern(defender.level, defender.mini_game, protocol="DMC_WINNER")
            loser_pattern = get_attack_pattern(attacker.level, attacker.mini_game, protocol="DMC_LOOSER")
            winner_name = defender.name
            loser_name = attacker.name

        # Simulate 5 turns
        for turn in range(5):
            # Winner attacks
            winner_damage = winner_pattern[turn]
            loser_hp = max(0, loser_device.hp - winner_damage)
            loser_device.hp = loser_hp

            # Loser attacks
            loser_damage = loser_pattern[turn]
            winner_hp = max(0, winner_device.hp - loser_damage)
            winner_device.hp = winner_hp

            # Log the turn
            turn_log = TurnLog(
                turn=turn + 1,
                device1_status=[
                    DigimonStatus(name=attacker.name, hp=dev_att.hp, alive=dev_att.hp > 0)
                ],
                device2_status=[
                    DigimonStatus(name=defender.name, hp=dev_def.hp, alive=dev_def.hp > 0)
                ],
                attacks=[
                    AttackLog(
                        turn=turn + 1,
                        device="device1" if winner_device == dev_att else "device2",
                        attacker=0,
                        defender=0,
                        hit=True,
                        damage=winner_damage
                    ),
                    AttackLog(
                        turn=turn + 1,
                        device="device1" if loser_device == dev_att else "device2",
                        attacker=0,
                        defender=0,
                        hit=True,
                        damage=loser_damage
                    )
                ]
            )
            battle_log.append(turn_log)

        # Step 7: Determine the winner
        winner = "device1" if outcome_device1 == 1 else "device2"

        # Step 8: Prepare the final result
        result = BattleResult(
            winner=winner,
            device1_final=[
                DigimonStatus(name=attacker.name, hp=dev_att.hp, alive=dev_att.hp > 0)
            ],
            device2_final=[
                DigimonStatus(name=defender.name, hp=dev_def.hp, alive=dev_def.hp > 0)
            ],
            battle_log=battle_log,
            device1_packets=device1_packets,
            device2_packets=device2_packets
        )

        return result

    def _simulate_dm20_bs(self, attacker: Digimon, defender: Digimon) -> BattleResult:
        """
        Simulates a battle using the Digital Monster Ver.20th protocol.
        """
        # Initialize DM20Device instances
        device1 = DM20Device(attacker)
        device2 = DM20Device(defender)

        # Constants
        EOL = 0b1110  # End of Line
        COU = 0b00    # Constant Or Unknown
        VERSION = 0b0001

        # Generate and exchange packets
        packets_device1 = []
        packets_device2 = []

        # Packet exchanges (1 to 9)
        packet1_device1 = device1.generate_packet1()
        packet1_device2 = device2.generate_packet1()
        device2.process_packet(packet1_device1)
        device1.process_packet(packet1_device2)
        packets_device1.append(packet1_device1)
        packets_device2.append(packet1_device2)

        packet2_device1 = device1.generate_packet2()
        packet2_device2 = device2.generate_packet2()
        device2.process_packet(packet2_device1)
        device1.process_packet(packet2_device2)
        packets_device1.append(packet2_device1)
        packets_device2.append(packet2_device2)

        packet3_device1 = device1.generate_packet3(order=1, version=VERSION, eol=EOL)
        packet3_device2 = device2.generate_packet3(order=0, version=VERSION, eol=EOL)
        device2.process_packet(packet3_device1)
        device1.process_packet(packet3_device2)
        packets_device1.append(packet3_device1)
        packets_device2.append(packet3_device2)

        packet4_device1 = device1.generate_packet4(cou=COU, eol=EOL)
        packet4_device2 = device2.generate_packet4(cou=COU, eol=EOL)
        device2.process_packet(packet4_device1)
        device1.process_packet(packet4_device2)
        packets_device1.append(packet4_device1)
        packets_device2.append(packet4_device2)

        packet5_device1 = device1.generate_packet5(eol=EOL)
        packet5_device2 = device2.generate_packet5(eol=EOL)
        device2.process_packet(packet5_device1)
        device1.process_packet(packet5_device2)
        packets_device1.append(packet5_device1)
        packets_device2.append(packet5_device2)

        packet6_device1 = device1.generate_packet6(cou=COU, eol=EOL)
        packet6_device2 = device2.generate_packet6(cou=COU, eol=EOL)
        device2.process_packet(packet6_device1)
        device1.process_packet(packet6_device2)
        packets_device1.append(packet6_device1)
        packets_device2.append(packet6_device2)

        packet7_device1 = device1.generate_packet7(cou=COU, eol=EOL)
        packet7_device2 = device2.generate_packet7(cou=COU, eol=EOL)
        device2.process_packet(packet7_device1)
        device1.process_packet(packet7_device2)
        packets_device1.append(packet7_device1)
        packets_device2.append(packet7_device2)

        packet8_device1 = device1.generate_packet8(eol=EOL)
        packet8_device2 = device2.generate_packet8(eol=EOL)
        device2.process_packet(packet8_device1)
        device1.process_packet(packet8_device2)
        packets_device1.append(packet8_device1)
        packets_device2.append(packet8_device2)

        packet9_device1 = device1.generate_packet9(eol=EOL)
        packet9_device2 = device2.generate_packet9(eol=EOL)
        device2.process_packet(packet9_device1)
        device1.process_packet(packet9_device2)
        packets_device1.append(packet9_device1)
        packets_device2.append(packet9_device2)

        # Packet A: Check, Dodges, Hits, EOL
        packetA_device1 = device1.generate_packetA(eol=EOL)
        packetA_device2 = device2.generate_packetA(eol=EOL)
        device2.process_packet(packetA_device1)
        device1.process_packet(packetA_device2)
        packets_device1.append(packetA_device1)
        packets_device2.append(packetA_device2)

        # Simulate the battle
        attacker_hp = 4
        defender_hp = 4
        battle_log = []

        # Retrieve attack patterns
        attack_pattern_device1 = get_dm20_attack_pattern(device1.digimon.tag_meter, device1.digimon.mini_game)
        attack_pattern_device2 = get_dm20_attack_pattern(device2.digimon.tag_meter, device2.digimon.mini_game)

        # Extract hits for both devices
        device1_hits = [(packetA_device1[1] >> (4 + i)) & 1 for i in range(4)]  # Extract MSB 4 bits from Packet A (Device 1)
        device2_hits = [(packetA_device2[1] >> (4 + i)) & 1 for i in range(4)]  # Extract MSB 4 bits from Packet A (Device 2)

        # Reverse the order of bits to match the turn order (MSB -> Turn 1, LSB -> Turn 4)
        device1_hits.reverse()
        device2_hits.reverse()

        # Simulate up to 6 turns
        for turn in range(6):
            # Determine the attack index (repeat 1st and 2nd attacks for turns 5 and 6)
            attack_index = turn % 4

            # Device 1 attacks Device 2
            device1_attack = attack_pattern_device1[attack_index]
            device1_hit = device1_hits[turn] if turn < 4 else device1_hits[turn % 4]
            defender_damage = device1_attack if device1_hit else 0
            defender_hp = max(0, defender_hp - defender_damage)

            # Device 2 attacks Device 1
            device2_attack = attack_pattern_device2[attack_index]
            device2_hit = device2_hits[turn] if turn < 4 else device2_hits[turn % 4]
            attacker_damage = device2_attack if device2_hit else 0
            attacker_hp = max(0, attacker_hp - attacker_damage)

            # Log the turn
            turn_log = TurnLog(
                turn=turn + 1,
                device1_status=[
                    DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
                ],
                device2_status=[
                    DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
                ],
                attacks=[
                    AttackLog(
                        turn=turn + 1,
                        device="device1",
                        attacker=0,
                        defender=0,
                        hit=bool(device1_hit),
                        damage=defender_damage
                    ),
                    AttackLog(
                        turn=turn + 1,
                        device="device2",
                        attacker=0,
                        defender=0,
                        hit=bool(device2_hit),
                        damage=attacker_damage
                    )
                ]
            )
            battle_log.append(turn_log)

            # End battle if both Digimon are defeated
            if attacker_hp == 0 and defender_hp == 0:
                # Device 1 attacks first, so it wins in case of a tie
                winner = "device1"
                break

            # End battle if one Digimon is defeated
            if attacker_hp == 0:
                winner = "device2"
                break
            elif defender_hp == 0:
                winner = "device1"
                break
        else:
            # If both are alive after 6 turns, winner is the one with highest HP
            if attacker_hp > defender_hp:
                winner = "device1"
            elif defender_hp > attacker_hp:
                winner = "device2"
            else:
                winner = "draw"

        # Prepare the final result
        result = BattleResult(
            winner=winner,
            device1_final=[
                DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
            ],
            device2_final=[
                DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
            ],
            battle_log=battle_log,
            device1_packets=packets_device1,
            device2_packets=packets_device2
        )

        return result
    
    def _simulate_pen20_bs(self, attacker: Digimon, defender: Digimon) -> BattleResult:
        """
        Simulates a battle using the Digital Monster Pen20th protocol.
        :param attacker: The attacking Digimon (device1).
        :param defender: The defending Digimon (device2).
        :return: A BattleResult object.
        """
        # Initialize Pen20Device instances
        device1 = Pen20Device(attacker)
        device2 = Pen20Device(defender)

        # Constants
        EOL = 0b1110  # End of Line
        COU = 0b00    # Constant Or Unknown
        VERSION = 0b0001

        # Generate and exchange packets
        packets_device1 = []
        packets_device2 = []

        # Packet exchanges (1 to 9)
        packet1_device1 = device1.generate_packet1(order=0, version=VERSION, eol=EOL)
        packet1_device2 = device2.generate_packet1(order=1, version=VERSION, eol=EOL)
        device2.process_packet(packet1_device1)
        device1.process_packet(packet1_device2)
        packets_device1.append(packet1_device1)
        packets_device2.append(packet1_device2)

        packet2_device1 = device1.generate_packet2(cou=COU, eol=EOL)
        packet2_device2 = device2.generate_packet2(cou=COU, eol=EOL)
        device2.process_packet(packet2_device1)
        device1.process_packet(packet2_device2)
        packets_device1.append(packet2_device1)
        packets_device2.append(packet2_device2)

        packet3_device1 = device1.generate_packet3(cou=COU, eol=EOL)
        packet3_device2 = device2.generate_packet3(cou=COU, eol=EOL)
        device2.process_packet(packet3_device1)
        device1.process_packet(packet3_device2)
        packets_device1.append(packet3_device1)
        packets_device2.append(packet3_device2)

        packet4_device1 = device1.generate_packet4(cou=COU, eol=EOL)
        packet4_device2 = device2.generate_packet4(cou=COU, eol=EOL)
        device2.process_packet(packet4_device1)
        device1.process_packet(packet4_device2)
        packets_device1.append(packet4_device1)
        packets_device2.append(packet4_device2)

        packet5_device1 = device1.generate_packet5(cou=COU, eol=EOL)
        packet5_device2 = device2.generate_packet5(cou=COU, eol=EOL)
        device2.process_packet(packet5_device1)
        device1.process_packet(packet5_device2)
        packets_device1.append(packet5_device1)
        packets_device2.append(packet5_device2)

        packet6_device1 = device1.generate_packet6(eol=EOL)
        packet6_device2 = device2.generate_packet6(eol=EOL)
        device2.process_packet(packet6_device1)
        device1.process_packet(packet6_device2)
        packets_device1.append(packet6_device1)
        packets_device2.append(packet6_device2)

        packet7_device1 = device1.generate_packet7(cou=COU, eol=EOL)
        packet7_device2 = device2.generate_packet7(cou=COU, eol=EOL)
        device2.process_packet(packet7_device1)
        device1.process_packet(packet7_device2)
        packets_device1.append(packet7_device1)
        packets_device2.append(packet7_device2)

        packet8_device1 = device1.generate_packet8(cou=COU, eol=EOL)
        packet8_device2 = device2.generate_packet8(cou=COU, eol=EOL)
        device2.process_packet(packet8_device1)
        device1.process_packet(packet8_device2)
        packets_device1.append(packet8_device1)
        packets_device2.append(packet8_device2)

        packet9_device1 = device1.generate_packet9(cou=COU, eol=EOL)
        packet9_device2 = device2.generate_packet9(cou=COU, eol=EOL)
        device2.process_packet(packet9_device1)
        device1.process_packet(packet9_device2)
        packets_device1.append(packet9_device1)
        packets_device2.append(packet9_device2)

        # Packet A: Check, Dodges, Hits, EOL
        packetA_device1 = device1.generate_packetA(eol=EOL)
        packetA_device2 = device2.generate_packetA(eol=EOL)
        device2.process_packet(packetA_device1)
        device1.process_packet(packetA_device2)
        packets_device1.append(packetA_device1)
        packets_device2.append(packetA_device2)

        # Simulate the battle
        attacker_hp = 3
        defender_hp = 3
        battle_log = []

        # Retrieve attack patterns
        attack_pattern_device1 = get_attack_pattern(0, 0, protocol="PEN20")
        attack_pattern_device2 = get_attack_pattern(0, 0, protocol="PEN20")

        # Extract hits for both devices
        device1_hits = [(packetA_device1[1] >> (4 + i)) & 1 for i in range(4)]  # Extract MSB 4 bits from Packet A (Device 1)
        device2_hits = [(packetA_device2[1] >> (4 + i)) & 1 for i in range(4)]  # Extract MSB 4 bits from Packet A (Device 2)

        # Reverse the order of bits to match the turn order (MSB -> Turn 1, LSB -> Turn 4)
        device1_hits.reverse()
        device2_hits.reverse()

        # Simulate up to 6 turns
        for turn in range(6):
            # Determine the attack index (repeat 1st and 2nd attacks for turns 5 and 6)
            attack_index = turn % 4

            # Device 1 attacks Device 2
            device1_attack = attack_pattern_device1[attack_index]
            device1_hit = device1_hits[turn] if turn < 4 else device1_hits[turn % 4]
            defender_damage = device1_attack if device1_hit else 0
            defender_hp = max(0, defender_hp - defender_damage)

            # Device 2 attacks Device 1
            device2_attack = attack_pattern_device2[attack_index]
            device2_hit = device2_hits[turn] if turn < 4 else device2_hits[turn % 4]
            attacker_damage = device2_attack if device2_hit else 0
            attacker_hp = max(0, attacker_hp - attacker_damage)

            # Log the turn
            turn_log = TurnLog(
                turn=turn + 1,
                device1_status=[
                    DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
                ],
                device2_status=[
                    DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
                ],
                attacks=[
                    AttackLog(
                        turn=turn + 1,
                        device="device1",
                        attacker=0,
                        defender=0,
                        hit=bool(device1_hit),
                        damage=defender_damage
                    ),
                    AttackLog(
                        turn=turn + 1,
                        device="device2",
                        attacker=0,
                        defender=0,
                        hit=bool(device2_hit),
                        damage=attacker_damage
                    )
                ]
            )
            battle_log.append(turn_log)

            # End battle if one Digimon is defeated
            if attacker_hp == 0 or defender_hp == 0:
                break

        # Determine the winner
        if attacker_hp > defender_hp:
            winner = "device1"
        elif defender_hp > attacker_hp:
            winner = "device2"
        else:
            winner = "draw"

        # Prepare the final result
        result = BattleResult(
            winner=winner,
            device1_final=[
                DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
            ],
            device2_final=[
                DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
            ],
            battle_log=battle_log,
            device1_packets=packets_device1,
            device2_packets=packets_device2
        )

        return result
    
    def _simulate_dmx_bs(self, attacker: Digimon, defender: Digimon) -> BattleResult:
        """
        Simulates a battle using the DMX protocol.
        """
        # Initialize DMXDevice instances
        device1 = DMXDevice(attacker)
        device2 = DMXDevice(defender)

        # Initialize packet storage
        packets_device1 = []
        packets_device2 = []

        # Packet exchanges
        # Packet 1: Order, Level, Sick, Attack, Version, EOL
        packet1_device1 = device1.generate_packet1()
        packet1_device2 = device2.generate_packet1()
        device2.process_packet(packet1_device1)
        device1.process_packet(packet1_device2)
        packets_device1.append(packet1_device1)
        packets_device2.append(packet1_device2)

        # Packet 2: Stage, Index, Attribute, EOL
        packet2_device1 = device1.generate_packet2()
        packet2_device2 = device2.generate_packet2()
        device2.process_packet(packet2_device1)
        device1.process_packet(packet2_device2)
        packets_device1.append(packet2_device1)
        packets_device2.append(packet2_device2)

        # Packet 3: Shot S, Shot W, EOL
        packet3_device1 = device1.generate_packet3()
        packet3_device2 = device2.generate_packet3()
        device2.process_packet(packet3_device1)
        device1.process_packet(packet3_device2)
        packets_device1.append(packet3_device1)
        packets_device2.append(packet3_device2)

        # Packet 4: COU, HP, Shot M, EOL
        packet4_device1 = device1.generate_packet4()
        packet4_device2 = device2.generate_packet4()
        device2.process_packet(packet4_device1)
        device1.process_packet(packet4_device2)
        packets_device1.append(packet4_device1)
        packets_device2.append(packet4_device2)

        # Packet 5: COU, Buff, Power, EOL
        packet5_device1 = device1.generate_packet5()
        packet5_device2 = device2.generate_packet5()
        device2.process_packet(packet5_device1)
        device1.process_packet(packet5_device2)
        packets_device1.append(packet5_device1)
        packets_device2.append(packet5_device2)

        # Packet 6: Check, COU, Hits, EOL
        packet6_device1 = device1.generate_packet6()
        packet6_device2 = device2.generate_packet6()
        device2.process_packet(packet6_device1)
        device1.process_packet(packet6_device2)
        packets_device1.append(packet6_device1)
        packets_device2.append(packet6_device2)

        # Extract hits for both devices
        device1_hits = [(device1.hits >> i) & 1 for i in range(4)]  # Extract 4 bits from hits
        device2_hits = [(device2.hits >> i) & 1 for i in range(4)]  # Extract 4 bits from hits

        # Reverse the order of bits to match the turn order (MSB -> Turn 1, LSB -> Turn 4)
        device1_hits.reverse()
        device2_hits.reverse()

        # Retrieve attack patterns for both devices
        attack_pattern_device1 = get_attack_pattern(device1.level, device1.digimon.mini_game, protocol="DMX")
        attack_pattern_device2 = get_attack_pattern(device2.level, device2.digimon.mini_game, protocol="DMX")

        # Simulate the battle
        attacker_hp = device1.hp
        defender_hp = device2.hp
        battle_log = []

        # Simulate up to 5 turns
        for turn in range(5):
            # Determine the attack index (repeat 1st and 2nd attacks for turns 5 and 6)
            attack_index = turn % 4

            # Device 1 attacks Device 2
            device1_attack = attack_pattern_device1[attack_index]
            device1_hit = device1_hits[attack_index]
            defender_damage = device1_attack if device1_hit else 0
            defender_hp = max(0, defender_hp - defender_damage)

            # Device 2 attacks Device 1
            device2_attack = attack_pattern_device2[attack_index]
            device2_hit = device2_hits[attack_index]
            attacker_damage = device2_attack if device2_hit else 0
            attacker_hp = max(0, attacker_hp - attacker_damage)

            # Log the turn
            turn_log = TurnLog(
                turn=turn + 1,
                device1_status=[
                    DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
                ],
                device2_status=[
                    DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
                ],
                attacks=[
                    AttackLog(
                        turn=turn + 1,
                        device="device1",
                        attacker=0,
                        defender=0,
                        hit=bool(device1_hit),
                        damage=defender_damage
                    ),
                    AttackLog(
                        turn=turn + 1,
                        device="device2",
                        attacker=0,
                        defender=0,
                        hit=bool(device2_hit),
                        damage=attacker_damage
                    )
                ]
            )
            battle_log.append(turn_log)

            # End battle if one Digimon is defeated
            if attacker_hp == 0 or defender_hp == 0:
                break

        # Determine the winner
        if attacker_hp > defender_hp:
            winner = "device1"
        elif defender_hp > attacker_hp:
            winner = "device2"
        else:
            winner = "draw"

        # Prepare the final result
        result = BattleResult(
            winner=winner,
            device1_final=[
                DigimonStatus(name=attacker.name, hp=attacker_hp, alive=attacker_hp > 0)
            ],
            device2_final=[
                DigimonStatus(name=defender.name, hp=defender_hp, alive=defender_hp > 0)
            ],
            battle_log=battle_log,
            device1_packets=packets_device1,
            device2_packets=packets_device2
        )

        return result
    
class DMCDevice:
    """
    Represents a Digimon device in a battle, able to generate and parse packets.
    """
    def __init__(self, data: Digimon):
        self.data = data
        self.hp = self.data.hp
        self.power = self.data.power
        self.attribute = self.data.attribute
        self.index = self.data.index
        self.shot = self.data.shot1
        self.packet_index = 0
        self.received_packets = []  # Store received packets

    def generate_packet1(self, operation):
        return DMCBSPacket(
            operation=operation,
            index=self.index,
            power=self.power,
            attribute=self.attribute,
            shot=self.shot,
            outcome=0
        ).build_packet1()

    def generate_packet2(self, operation, outcome):
        return DMCBSPacket(
            operation=operation,
            index=self.index,
            power=self.power,
            attribute=self.attribute,
            shot=self.shot,
            outcome=outcome
        ).build_packet2()

    def process_packet(self, packet):
        """
        Processes an incoming packet and stores it for later use.
        """
        self.received_packets.append(packet)

    def calculate_outcome(self, opponent):
        """
        Calculates the battle outcome based on the exchanged data.
        """
        # Example logic: Compare power and attribute advantage
        advantage = 0
        if (self.attribute == 0 and opponent.attribute == 2) or \
           (self.attribute == 1 and opponent.attribute == 0) or \
           (self.attribute == 2 and opponent.attribute == 1):
            advantage = 5  # Example attribute advantage

        hitrate = ((self.power * 100) / (self.power + opponent.power)) + advantage
        hitrate = max(0, min(hitrate, 100))  # Clamp hitrate between 0 and 100

        # Simulate attack roll
        attack_roll = random.randint(0, 99)
        return 1 if attack_roll < hitrate else 0  # 1 = win, 0 = lose
    
class DM20Device:
    """
    Represents a Digimon device in the DM20_BS protocol.
    Handles packet generation, processing, and state management.
    """
    def __init__(self, digimon: Digimon):
        self.digimon = digimon
        self.hp = digimon.hp
        self.power = digimon.power
        self.attribute = digimon.attribute
        self.index = digimon.index
        self.shot1 = digimon.shot1
        self.shot2 = digimon.shot2
        self.tag_meter = digimon.tag_meter  # Use the tag_meter attribute from the Digimon class
        self.packets = []  # Stores packets received from the opponent
        self.opponent_data = []  # Store opponent's data

    def generate_packet1(self):
        """
        Generates Packet 1: Name 2, Name 1.
        """
        tamer_name = ["O", "M", "N", "I"]
        return struct.pack(">BB", ord(tamer_name[1]), ord(tamer_name[0]))

    def generate_packet2(self):
        """
        Generates Packet 2: Name 4, Name 3.
        """
        tamer_name = ["O", "M", "N", "I"]
        return struct.pack(">BB", ord(tamer_name[3]), ord(tamer_name[2]))

    def generate_packet3(self, order, version, eol):
        """
        Generates Packet 3: Order, Attack (Mini-Game Taps), Operation, Version, EOL.
        """
        attack = self.digimon.mini_game  # Use the mini-game taps value
        operation = 0b00  # Single Battle
        return struct.pack(">B", (order << 7) | (attack << 2) | operation) + struct.pack(">B", (version << 4) | eol)

    def generate_packet4(self, cou, eol):
        """
        Generates Packet 4: COU, Index L, Attribute L, EOL.
        """
        return struct.pack(">B", (cou << 6) | self.index) + struct.pack(">B", (self.attribute << 4) | eol)

    def generate_packet5(self, eol):
        """
        Generates Packet 5: Shot S L, Shot W L, EOL.
        """
        return struct.pack(">BBB", self.shot1, self.shot2, eol)

    def generate_packet6(self, cou, eol):
        """
        Generates Packet 6: COU, Power L, EOL.
        """
        return struct.pack(">B", (cou << 6) | (self.power & 0b111111)) + struct.pack(">B", eol)

    def generate_packet7(self, cou, eol):
        """
        Generates Packet 7: COU, Index R, Attribute R, EOL.
        """
        index_r = 0  # For single battles, R values are 0
        attribute_r = 0  # For single battles, R values are 0
        return struct.pack(">B", (cou << 6) | index_r) + struct.pack(">B", (attribute_r << 4) | eol)

    def generate_packet8(self, eol):
        """
        Generates Packet 8: Shot S R, Shot W R, EOL.
        """
        shot_s_r = 0  # For single battles, R values are 0
        shot_w_r = 0  # For single battles, R values are 0
        return struct.pack(">B", (shot_s_r << 2) | (shot_w_r >> 4)) + struct.pack(">B", ((shot_w_r & 0b1111) << 4) | eol)

    def generate_packet9(self, eol):
        """
        Generates Packet 9: Tag Meter, Power R, EOL.
        """
        tag_meter = self.digimon.tag_meter  # Use the tag_meter attribute from the Digimon class
        power_r = 0  # For single battles, Power R is 0
        return struct.pack(">B", (tag_meter << 4) | (power_r >> 4)) + struct.pack(">B", ((power_r & 0b1111) << 4) | eol)

    def process_packet(self, packet):
        """
        Processes an incoming packet and stores it for later use.
        """
        self.opponent_data.append(packet)

    def generate_packetA(self, eol):
        """
        Generates Packet A: Check, Dodges, Hits, EOL.
        """
        if not self.opponent_data:
            raise ValueError("Opponent data is not available. Ensure packets are processed before generating Packet A.")

        # Extract opponent's power and attribute from the stored packets
        opponent_power = self.opponent_data[4][0] & 0b11111111  # Power from Packet 5
        opponent_attribute = (self.opponent_data[1][1] >> 4) & 0b1111  # Attribute from Packet 2

        power = self.digimon.power
        if (self.digimon.attribute == 0 and opponent_attribute == 2) or \
           (self.digimon.attribute == 1 and opponent_attribute == 0) or \
           (self.digimon.attribute == 2 and opponent_attribute == 1):
            power += 32  # Attribute advantage

        # Add 32 to opponent's power if they have an attribute advantage
        if (opponent_attribute == 0 and self.digimon.attribute == 2) or \
           (opponent_attribute == 1 and self.digimon.attribute == 0) or \
           (opponent_attribute == 2 and self.digimon.attribute == 1):
            opponent_power += 32

        # Initialize hits and dodges
        hits = 0
        dodges = 0

        # Calculate hits and dodges for 4 attacks
        for i in range(4):
            # Calculate hitrate
            hitrate = ((power * 100) / (power + opponent_power))
            hitrate = max(0, min(hitrate, 100))  # Clamp hitrate between 0 and 100

            # Simulate hit
            attack_roll = random.randint(0, 99)
            hit = 1 if attack_roll < hitrate else 0

            # Calculate dodge (inverted for single battles)
            dodge = 1 - hit

            # Update hits and dodges bit patterns (right to left)
            hits |= (hit << i)
            dodges |= (dodge << i)

        check = self._calculate_check(hits, dodges, eol)

        # Pack the data into bytes
        return struct.pack(">B", (check << 4) | dodges) + struct.pack(">B", (hits << 4) | eol)

    def _calculate_check(self, hits, dodges, eol):
        """
        Calculates the Check value for Packet A.
        Ensures the intended remainder when the sum of all 4-bit groups is divided by 16.
        """
        # Sum all 4-bit groups
        total_sum = (hits & 0b1111) + (dodges & 0b1111) + (eol & 0b1111)

        # Intended remainder (example: 11)
        intended_remainder = 11

        # Calculate the Check value
        check = (intended_remainder - (total_sum % 16)) % 16
        return check

class DMCBSPacket:
    """
    Represents a DMC_BS packet (2 packets per exchange).
    """
    COU = 0x47444C43  # 'DMCL'

    def __init__(self, operation: int, index: int, power: int, attribute: int, shot: int, outcome: int):
        self.operation = operation  # Operation code (0-3)
        self.index = index          # Digimon index
        self.power = power          # Digimon power
        self.attribute = attribute  # Digimon attribute (0=Free, 1=Virus, 2=Data, 3=Vaccine)
        self.shot = shot            # Attack sprite ID
        self.outcome = outcome      # Battle outcome (0=loss, 1=win)

    def _calc_check(self, packet_bytes: bytes) -> int:
        """
        Calculates the checksum for the packet.
        The checksum is the sum of all 16-bit fields, keeping only the lowest 16 bits.
        """
        check = 0
        for i in range(0, len(packet_bytes) - 2, 2):  # Exclude the last 2 bytes (checksum field)
            segment = int.from_bytes(packet_bytes[i:i+2], 'big')
            check += segment
        return check & 0xFFFF  # Keep only the lowest 16 bits

    def build_packet1(self) -> bytes:
        """
        Builds Packet 1 (Digimon Data Packet).
        Structure:
        COU (4 bytes) | Operation (2 bytes) | Version (2 bytes) | Index (2 bytes) |
        Power (2 bytes) | Attribute (2 bytes) | Check (2 bytes)
        """
        version = 1  # Fixed version value
        packet = struct.pack(">IHHHHHH",
            self.COU,           # COU (4 bytes)
            self.operation,     # Operation (2 bytes)
            version,            # Version (2 bytes)
            self.index,         # Index (2 bytes)
            self.power,         # Power (2 bytes)
            self.attribute,     # Attribute (2 bytes)
            0                   # Check (placeholder, 2 bytes)
        )
        check = self._calc_check(packet)
        return struct.pack(">IHHHHHH",
            self.COU,
            self.operation,
            version,
            self.index,
            self.power,
            self.attribute,
            check                # Final checksum
        )

    def build_packet2(self) -> bytes:
        """
        Builds Packet 2 (Battle Data Packet).
        Structure:
        COU (4 bytes) | Operation (2 bytes) | Shot (2 bytes) | Outcome (2 bytes) |
        COU (4 bytes) | Check (2 bytes)
        """
        packet = struct.pack(">IHHHIH",
            self.COU,           # COU (4 bytes)
            self.operation,     # Operation (2 bytes)
            self.shot,          # Shot (2 bytes)
            self.outcome,       # Outcome (2 bytes)
            0,                  # Placeholder for repeated COU (4 bytes)
            0                   # Check (placeholder, 2 bytes)
        )
        check = self._calc_check(packet)
        return struct.pack(">IHHHIH",
            self.COU,
            self.operation,
            self.shot,
            self.outcome,
            0,                  # Placeholder for repeated COU
            check                # Final checksum
        )

class Pen20Device:
    """
    Represents a Digimon device in the Pen20_BS protocol.
    Handles packet generation, processing, and state management.
    """
    def __init__(self, digimon: Digimon):
        self.digimon = digimon
        self.hp = digimon.hp
        self.power = digimon.power
        self.attribute = digimon.attribute
        self.index = digimon.index
        self.shot1 = digimon.shot1
        self.shot2 = digimon.shot2
        self.traited = digimon.traited  # Trait status of the Digimon
        self.egg_shake = digimon.egg_shake  # Egg shake status of
        self.sick = digimon.sick  # Sick status of the Digimon
        self.tag_meter = digimon.tag_meter  # Use the tag_meter attribute from the Digimon class
        self.packets = []  # Stores packets received from the opponent
        self.opponent_data = []  # Store opponent's data

    def generate_packet1(self, order, version, eol):
        """
        Generates Packet 1: Order, COU, Attack, Operation, Version, EOL.
        """
        attack = self.digimon.mini_game  # Use the mini-game taps value
        operation = 0b00  # Single Battle
        cou = 0b0  # Constant or unknown (always 0)

        # Pack the data into two bytes
        return struct.pack(
            ">B", (order << 7) | (cou << 6) | (attack << 2) | operation
        ) + struct.pack(
            ">B", (version << 4) | eol
        )

    def generate_packet2(self, cou, eol):
        """
        Generates Packet 2: COU, Index L, Attribute L, EOL.
        """
        return struct.pack(
            ">B", (cou << 6) | self.index
        ) + struct.pack(
            ">B", (self.attribute << 4) | eol
        )

    def generate_packet3(self, cou, eol):
        """
        Generates Packet 3: COU, Shot W L, EOL.
        """
        return struct.pack(
            ">B", (cou << 4) | (self.shot2 >> 4)
        ) + struct.pack(
            ">B", ((self.shot2 & 0b1111) << 4) | eol
        )

    def generate_packet4(self, cou, eol):
        """
        Generates Packet 4: Sick, COU, Shot S L, EOL.
        """
        return struct.pack(
            ">B", (self.sick << 7) | (cou << 4) | (self.shot1 >> 4)
        ) + struct.pack(
            ">B", ((self.shot1 & 0b1111) << 4) | eol
        )

    def generate_packet5(self, cou, eol):
        """
        Generates Packet 5: COU, Traited, Egg Shake, Power L, EOL.
        """
        return struct.pack(
            ">B", (cou << 6) | (self.traited << 5) | (self.egg_shake << 4) | (self.power & 0b1111_1111)
        ) + struct.pack(
            ">B", eol
        )

    def generate_packet6(self, eol):
        """
        Generates Packet 6: Copy, Index R, Attribute R, EOL.
        """
        index_r = 0  # For single battles, Index R is 0
        attribute_r = 0  # For single battles, Attribute R is 0
        return struct.pack(
            ">B", (0 << 6) | index_r
        ) + struct.pack(
            ">B", (attribute_r << 4) | eol
        )

    def generate_packet7(self, cou, eol):
        """
        Generates Packet 7: COU, Shot W R, EOL.
        """
        shot_w_r = 0  # For single battles, Shot W R is 0
        return struct.pack(
            ">B", (cou << 4) | (shot_w_r >> 4)
        ) + struct.pack(
            ">B", ((shot_w_r & 0b1111) << 4) | eol
        )

    def generate_packet8(self, cou, eol):
        """
        Generates Packet 8: COU, Shot S R, EOL.
        """
        shot_s_r = 0  # For single battles, Shot S R is 0
        return struct.pack(
            ">B", (cou << 4) | (shot_s_r >> 4)
        ) + struct.pack(
            ">B", ((shot_s_r & 0b1111) << 4) | eol
        )

    def generate_packet9(self, cou, eol):
        """
        Generates Packet 9: COU, Power R, EOL.
        """
        power_r = 0  # For single battles, Power R is 0
        return struct.pack(
            ">B", (cou << 4) | (power_r >> 4)
        ) + struct.pack(
            ">B", ((power_r & 0b1111) << 4) | eol
        )

    def process_packet(self, packet):
        """
        Processes an incoming packet and stores it for later use.
        """
        self.opponent_data.append(packet)

    def generate_packetA(self, eol):
        """
        Generates Packet A: Check, Dodges, Hits, EOL.
        """
        if not self.opponent_data:
            raise ValueError("Opponent data is not available. Ensure packets are processed before generating Packet A.")

        # Extract opponent's power and attribute from the stored packets
        opponent_power = self.opponent_data[4][0] & 0b11111111  # Power from Packet 5
        opponent_attribute = (self.opponent_data[1][1] >> 4) & 0b1111  # Attribute from Packet 2

        power = self.digimon.power
        if (self.digimon.attribute == 0 and opponent_attribute == 2) or \
           (self.digimon.attribute == 1 and opponent_attribute == 0) or \
           (self.digimon.attribute == 2 and opponent_attribute == 1):
            power += 32  # Attribute advantage

        # Add 32 to opponent's power if they have an attribute advantage
        if (opponent_attribute == 0 and self.digimon.attribute == 2) or \
           (opponent_attribute == 1 and self.digimon.attribute == 0) or \
           (opponent_attribute == 2 and self.digimon.attribute == 1):
            opponent_power += 32

        # Initialize hits and dodges
        hits = 0
        dodges = 0

        # Calculate hits and dodges for 4 attacks
        for i in range(4):
            # Calculate hitrate
            hitrate = ((power * 100) / (power + opponent_power))
            hitrate = max(0, min(hitrate, 100))  # Clamp hitrate between 0 and 100

            # Simulate hit
            attack_roll = random.randint(0, 99)
            hit = 1 if attack_roll < hitrate else 0

            # Calculate dodge (inverted for single battles)
            dodge = 1 - hit

            # Update hits and dodges bit patterns (right to left)
            hits |= (hit << i)
            dodges |= (dodge << i)

        check = self._calculate_check(hits, dodges, eol)

        # Pack the data into bytes
        return struct.pack(">B", (check << 4) | dodges) + struct.pack(">B", (hits << 4) | eol)

    def _calculate_check(self, hits, dodges, eol):
        """
        Calculates the Check value for Packet A.
        Ensures the intended remainder when the sum of all 4-bit groups is divided by 16.
        """
        # Sum all 4-bit groups
        total_sum = (hits & 0b1111) + (dodges & 0b1111) + (eol & 0b1111)

        # Intended remainder (example: 11)
        intended_remainder = 11

        # Calculate the Check value
        check = (intended_remainder - (total_sum % 16)) % 16
        return check

class DMXDevice:
    """
    Represents a Digimon device in the DMX protocol.
    Handles packet generation, processing, and state management.
    """
    def __init__(self, digimon: Digimon):
        self.digimon = digimon
        self.hp = digimon.hp
        self.power = digimon.power
        self.attribute = digimon.attribute
        self.level = digimon.level
        self.sick = digimon.sick
        self.stage = digimon.stage
        self.index = digimon.index
        self.shot_s = digimon.shot1
        self.shot_w = digimon.shot2
        self.shot_m = digimon.shot1
        self.buff = digimon.buff
        self.order = digimon.order
        self.version = 0b0000 #Version 1 - Black
        self.hits = 0  # Hit pattern
        self.check = 0  # Check value
        self.received_packets = []  # Store received packets

    def generate_packet1(self):
        """
        Generates Packet 1: Order, Level, Sick, Attack, Version, EOL.
        """
        attack = self.digimon.mini_game
        return struct.pack(
            ">B", (self.order << 7) | (self.level << 3) | (self.sick << 1) | (attack >> 5)
        ) + struct.pack(
            ">B", ((attack & 0b11111) << 3) | self.version
        )

    def generate_packet2(self):
        """
        Generates Packet 2: Stage, Index, Attribute, EOL.
        """
        return struct.pack(
            ">B", (self.stage << 5) | (self.index >> 3)
        ) + struct.pack(
            ">B", ((self.index & 0b111) << 5) | (self.attribute << 3) | 0b1110
        )

    def generate_packet3(self):
        """
        Generates Packet 3: Shot S, Shot W, EOL.
        """
        return struct.pack(
            ">B", self.shot_s
        ) + struct.pack(
            ">B", self.shot_w
        ) + struct.pack(
            ">B", 0b1110  # EOL
        )

    def generate_packet4(self):
        """
        Generates Packet 4: COU, HP, Shot M, EOL.
        """
        return struct.pack(
            ">B", (0b00 << 6) | (self.hp << 1) | (self.shot_m >> 4)
        ) + struct.pack(
            ">B", ((self.shot_m & 0b1111) << 4) | 0b1110
        )

    def generate_packet5(self):
        """
        Generates Packet 5: COU, Buff, Power, EOL.
        """
        return struct.pack(
            ">B", (0b00 << 6) | (self.buff << 4)
        ) + struct.pack(
            ">B", self.power
        ) + struct.pack(
            ">B", 0b1110  # EOL
        )

    def generate_packet6(self, eol=0b1110):
        """
        Generates Packet 6: Check, COU, Hits, EOL.
        Extracts opponent's power and attribute from received packets.
        """
        if len(self.received_packets) < 2:
            raise ValueError("Not enough packets received to calculate opponent's power and attribute.")

        # Extract opponent's power from Packet 5 (second byte of the packet)
        opponent_power = self.received_packets[4][1]  # Assuming Packet 5 is at index 4

        # Extract opponent's attribute from Packet 2 (second byte of the packet, upper 4 bits)
        opponent_attribute = (self.received_packets[1][1] >> 4) & 0b1111  # Assuming Packet 2 is at index 1

        # Apply attribute advantage
        player_power = self.power
        if (self.attribute == 0 and opponent_attribute == 2) or \
           (self.attribute == 1 and opponent_attribute == 0) or \
           (self.attribute == 2 and opponent_attribute == 1):
            player_power += 32  # Attribute advantage

        if (opponent_attribute == 0 and self.attribute == 2) or \
           (opponent_attribute == 1 and self.attribute == 0) or \
           (opponent_attribute == 2 and self.attribute == 1):
            opponent_power += 32  # Opponent's attribute advantage

        # Calculate hits
        hits = 0
        for i in range(4):  # Simulate 4 attacks
            hitrate = ((player_power * 100) / (player_power + opponent_power))
            hitrate = max(0, min(hitrate, 100))  # Clamp hitrate between 0 and 100

            # Simulate hit
            attack_roll = random.randint(0, 99)
            hit = 1 if attack_roll < hitrate else 0

            # Update hits bit pattern (right to left)
            hits |= (hit << i)

        self.hits = hits

        # Calculate Check value
        total_sum = (self.hits & 0b1111) + (0b000 & 0b1111) + (eol & 0b1111)
        intended_remainder = 11  # Example remainder
        self.check = (intended_remainder - (total_sum % 16)) % 16

        # Pack the data into bytes
        return struct.pack(
            ">B", (self.check << 4) | (0b000 << 1) | (self.hits >> 4)
        ) + struct.pack(
            ">B", ((self.hits & 0b1111) << 4) | eol
        )

    def process_packet(self, packet):
        """
        Processes an incoming packet and stores it for later use.
        """
        self.received_packets.append(packet)

    def calculate_check(self):
        """
        Calculates the Check value for Packet 6.
        """
        total_sum = (self.hits & 0b1111) + (0b000 & 0b1111) + (0b1110 & 0b1111)
        intended_remainder = 11
        self.check = (intended_remainder - (total_sum % 16)) % 16

# --- Test code ---
if __name__ == "__main__":
    # Test Digimon data using the Digimon model
    device1 = Digimon(
        name="Agumon",
        order=0,
        traited=0,
        egg_shake=0,
        index=2,
        hp=6,
        attribute=0,  # Vaccine
        power=50,
        handicap=0,
        buff=0,
        mini_game=0,
        level=5,
        stage=0,
        sick=0,
        shot1=80,  # Stronger attack sprite ID
        shot2=85,   # Weaker attack sprite ID
        tag_meter=2  # Example value for Tag Meter
    )

    device2 = Digimon(
        name="Gabumon",
        order=0,
        traited=0,
        egg_shake=0,
        index=18,
        hp=6,
        attribute=2,  # Virus
        power=45,
        handicap=0,
        buff=0,
        mini_game=3,
        level=5,
        stage=0,
        sick=0,
        shot1=70,  # Stronger attack sprite ID
        shot2=75,   # Weaker attack sprite ID
        tag_meter=2  # Example value for Tag Meter
    )

    simulator = BattleSimulator(protocol=BattleProtocol.DM20_BS)
    result = simulator.simulate(device1, device2)