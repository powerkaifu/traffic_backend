import sys
import tensorflow as tf

print(f"Python: {sys.version}")
print(f"TensorFlow: {tf.__version__}")
print(f"GPU Available: {bool(tf.config.list_physical_devices('GPU'))}")