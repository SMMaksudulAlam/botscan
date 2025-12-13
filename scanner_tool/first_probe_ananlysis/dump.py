import pickle

def read_and_process_file(input_filename, output_filename):
    list_of_lists = []

    with open(input_filename, 'r') as file:
        for line in file:
            elements = [element.strip() for element in line.strip().split(',')]
            list_of_lists.append(elements)
    print(list_of_lists)
    with open(output_filename, 'wb') as pkl_file:
        pickle.dump(list_of_lists, pkl_file)

input_filename = 'first_probe.txt'
output_filename = 'first_probe.pkl'
read_and_process_file(input_filename, output_filename)

