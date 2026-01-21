from graphviz import Digraph
import os

def generate_er_diagram():
    # Create a new directed graph
    dot = Digraph(comment='QR Code Menu System ER Diagram')
    dot.attr(rankdir='LR')  # Left to right direction
    
    # Set node styles
    dot.attr('node', shape='rectangle', style='rounded')
    
    # Add User table
    dot.node('User', '''User
    id: Integer (PK)
    email: String
    password: String
    restaurant_name: String
    logo_filename: String
    qr_filename: String''')
    
    # Add MenuItem table
    dot.node('MenuItem', '''MenuItem
    id: Integer (PK)
    name: String
    description: Text
    price: Float
    image_filename: String
    user_id: Integer (FK)''')
    
    # Add Order table
    dot.node('Order', '''Order
    id: Integer (PK)
    table_number: String
    items: Text
    special_instructions: Text
    user_id: Integer (FK)
    created_at: DateTime
    status: String''')
    
    # Add relationships
    dot.edge('User', 'MenuItem', '1:N')
    dot.edge('User', 'Order', '1:N')
    
    # Save the diagram
    dot.render('er_diagram', format='png', cleanup=True)
    print("ER diagram has been generated as 'er_diagram.png'")

if __name__ == '__main__':
    generate_er_diagram() 