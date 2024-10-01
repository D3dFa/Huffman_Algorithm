import heapq
import argparse
from collections import defaultdict
import struct

class Node:
    def __init__(self, freq, char=None, left=None, right=None):
        self.freq = freq  # Частота символа
        self.char = char  # Символ (для листьев)
        self.left = left  # Левый потомок
        self.right = right  # Правый потомок

    def __lt__(self, other):
        return self.freq < other.freq

def build_frequency_table(text):
    frequency = defaultdict(int)
    for char in text:
        frequency[char] += 1
    return frequency

def build_huffman_tree(frequency):
    heap = []
    for char, freq in frequency.items():
        heapq.heappush(heap, Node(freq, char))
    if len(heap) == 0:
        return None
    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = Node(node1.freq + node2.freq, None, node1, node2)
        heapq.heappush(heap, merged)
    return heap[0]

def build_codes(node, prefix="", codebook=None):
    if codebook is None:
        codebook = {}
    if node is not None:
        if node.char is not None:
            codebook[node.char] = prefix or "0"  # Обработка случая одного символа
        build_codes(node.left, prefix + "0", codebook)
        build_codes(node.right, prefix + "1", codebook)
    return codebook

def encode(text, codebook):
    return ''.join(codebook[char] for char in text)

def decode(encoded_bits, root):
    decoded = []
    node = root
    for bit in encoded_bits:
        node = node.left if bit == '0' else node.right
        if node.char is not None:
            decoded.append(node.char)
            node = root
    return ''.join(decoded)

def serialize_tree(node):
    """Сериализует дерево в префиксном порядке с использованием '1' для листьев и '0' для внутренних узлов.
    Возвращает байтовую строку."""
    bits = []
    def _serialize(node):
        if node is None:
            return
        if node.char is not None:
            bits.append('1')
            char_bits = format(ord(node.char), '08b')
            bits.extend(char_bits)
        else:
            bits.append('0')
            _serialize(node.left)
            _serialize(node.right)
    _serialize(node)
    bit_string = ''.join(bits)
    return bit_string_to_bytes(bit_string)

def deserialize_tree(bit_bytes):
    """Десериализует дерево из байтовой строки.
    Возвращает корень дерева."""
    bit_string = bytes_to_bit_string(bit_bytes)
    def _deserialize(it):
        try:
            bit = next(it)
        except StopIteration:
            return None
        if bit == '1':
            char_bits = ''.join(next(it) for _ in range(8))
            return Node(0, chr(int(char_bits, 2)))
        else:
            left = _deserialize(it)
            right = _deserialize(it)
            return Node(0, None, left, right)
    return _deserialize(iter(bit_string))

def bit_string_to_bytes(s):
    """Преобразует строку битов в байты."""
    padding = (8 - len(s) % 8) % 8
    s += '0' * padding
    byte_array = bytearray()
    for i in range(0, len(s), 8):
        byte = s[i:i+8]
        byte_array.append(int(byte, 2))
    return bytes([padding]) + bytes(byte_array)  # Первый байт хранит количество добавленных нулей

def bytes_to_bit_string(b):
    """Преобразует байты в строку битов, учитывая количество заполненных битов."""
    padding = b[0]
    bit_string = ''.join(f'{byte:08b}' for byte in b[1:])
    if padding > 0:
        bit_string = bit_string[:-padding]
    return bit_string

def save_encoded_file(encoded_bits, tree_bits, output_file):
    """Сохраняет закодированные данные вместе с сериализованным деревом в бинарном формате."""
    with open(output_file, 'wb') as f:
        # Сначала записываем длину дерева в байтах
        tree_length = len(tree_bits)
        f.write(struct.pack('>I', tree_length))  # 4 байта для длины
        # Записываем сериализованное дерево
        f.write(tree_bits)
        # Записываем закодированные данные
        f.write(encoded_bits)

def load_encoded_file(input_file):
    """Загружает закодированные данные и сериализованное дерево из бинарного файла."""
    with open(input_file, 'rb') as f:
        # Считываем первые 4 байта для длины дерева
        tree_length_bytes = f.read(4)
        if len(tree_length_bytes) < 4:
            raise ValueError("Файл поврежден или некорректен.")
        tree_length = struct.unpack('>I', tree_length_bytes)[0]
        # Считываем сериализованное дерево
        tree_bits = f.read(tree_length)
        # Считываем закодированные данные
        encoded_bits = f.read()
    return tree_bits, encoded_bits

def display_codes(codebook):
    print("Коды Хаффмана:")
    for char, code in sorted(codebook.items()):
        if char == ' ':
            display_char = "' ' (пробел)"
        elif char == '\n':
            display_char = "'\\n' (новая строка)"
        else:
            display_char = repr(char)
        print(f"{display_char}: {code}")

def display_tree(node, prefix=''):
    """Рекурсивный вывод дерева Хаффмана."""
    if node is not None:
        if node.char is not None:
            print(f"{prefix}Leaf: {repr(node.char)}")
        else:
            print(f"{prefix}Node:")
            display_tree(node.left, prefix + " 0-")
            display_tree(node.right, prefix + " 1-")

def encode_file(input_file, output_file, display=False, display_tree_flag=False):
    with open(input_file, 'r', encoding='ascii') as f:
        text = f.read()
    frequency = build_frequency_table(text)
    tree = build_huffman_tree(frequency)
    if tree is None:
        print("Входной файл пуст.")
        return
    codebook = build_codes(tree)
    encoded_bit_string = encode(text, codebook)
    encoded_bits = bit_string_to_bytes(encoded_bit_string)
    tree_bits = serialize_tree(tree)
    save_encoded_file(encoded_bits, tree_bits, output_file)
    if display:
        display_codes(codebook)
    if display_tree_flag:
        print("Дерево Хаффмана:")
        display_tree(tree)

def decode_file(input_file, output_file, display=False, display_tree_flag=False):
    tree_bits, encoded_bits = load_encoded_file(input_file)
    tree = deserialize_tree(tree_bits)
    if tree is None:
        print("Входной файл не содержит данных для декодирования.")
        return
    if display_tree_flag:
        print("Дерево Хаффмана:")
        display_tree(tree)
    encoded_bit_string = bytes_to_bit_string(encoded_bits)
    decoded_text = decode(encoded_bit_string, tree)
    with open(output_file, 'w', encoding='ascii') as f:
        f.write(decoded_text)
    if display:
        print("Декодированный текст:")
        print(decoded_text)

def main():
    parser = argparse.ArgumentParser(description="Система кодирования и декодирования с использованием алгоритма Хаффмана.")
    subparsers = parser.add_subparsers(dest='command', help='Команда: encode или decode')

    # Подкоманда encode
    encode_parser = subparsers.add_parser('encode', help='Кодирование файла')
    encode_parser.add_argument('input', help='Входной текстовый файл для кодирования')
    encode_parser.add_argument('output', help='Выходной файл с закодированными данными')
    encode_parser.add_argument('-c', '--codes', action='store_true', help='Отобразить коды Хаффмана')
    encode_parser.add_argument('-t', '--tree', action='store_true', help='Отобразить дерево Хаффмана')

    # Подкоманда decode
    decode_parser = subparsers.add_parser('decode', help='Декодирование файла')
    decode_parser.add_argument('input', help='Входной файл с закодированными данными')
    decode_parser.add_argument('output', help='Выходной текстовый файл с декодированными данными')
    decode_parser.add_argument('-c', '--codes', action='store_true', help='Отобразить декодированный текст')
    decode_parser.add_argument('-t', '--tree', action='store_true', help='Отобразить дерево Хаффмана')

    args = parser.parse_args()

    if args.command == 'encode':
        encode_file(args.input, args.output, display=args.codes, display_tree_flag=args.tree)
    elif args.command == 'decode':
        decode_file(args.input, args.output, display=args.codes, display_tree_flag=args.tree)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
