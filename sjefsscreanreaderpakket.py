import accessible_output2
from accessible_output2.outputs.auto import Auto

Auto().output("Hello, world!")

# Initialize the Braille output
braille_output = Braille()

# Send a message to the Braille display
braille_output.output("Hi Kevin, this is Braille!")
