import gc, os, time

import machine
from machine import Pin, I2C, TouchPad

import ssd1306

# OLED display
i2c = I2C(-1, scl=Pin(22), sda=Pin(21))
oled_width = 128
oled_height = 32
font_px = 8
page_size = oled_height//font_px
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)

# touch pins
touch_left_pin = Pin(14, Pin.IN)#, Pin.PULL_DOWN)
touch_middle_pin = Pin(12, Pin.IN)#, Pin.PULL_DOWN) # doesn't work as touch
touch_right_pin = Pin(13, Pin.IN)#, Pin.PULL_DOWN)
touch_left = TouchPad(touch_left_pin)
touch_middle = TouchPad(touch_middle_pin)
touch_right = TouchPad(touch_right_pin)
#touch_left.config(800)
#touch_middle.config(800)
#touch_right.config(800)

# touch0.config(600)  # I think 0 is default sensitivity and higher is less sensitive
# touch0.read()




def center(msg):
  return (oled_width - font_px*len(msg))//2


class State(object):
  SELECT = 1
  PLAY = 2


class Note(object):

  midi_note = {}
  ALL = []
  
  PULSE_MS = 50

  def __init__(self, name, midi_note, pin_number, pulse_ms=None):
    self.name = name
    self.midi_note = midi_note
    self.pulse_ms =  pulse_ms or Note.PULSE_MS
    print('Note', name, 'midi', midi_note, 'at pin ', pin_number)
    self.pin = machine.Pin(pin_number, machine.Pin.OUT, machine.Pin.PULL_DOWN)
    Note.midi_note[midi_note] = self
    Note.ALL.append(self)
    
  def play(self, pulse_ms=None):
    if pulse_ms is None: pulse_ms = self.pulse_ms
    print('', self.name, '\t', pulse_ms)
    self.pin.on()
    time.sleep_ms(pulse_ms)
    self.pin.off()


c = Note('C', 60, 15, pulse_ms=70)
d = Note('D', 62, 2, pulse_ms=100)
e = Note('E', 64, 4, pulse_ms=40)
f = Note('F', 65, 27, pulse_ms=50)
fs = Note('F#', 66, 26, pulse_ms=20)
g = Note('G', 67, 25, pulse_ms=40)
a = Note('A', 69, 33, pulse_ms=20)
b = Note('B', 71, 32, pulse_ms=20)
hc = Note('^C', 72, 16, pulse_ms=30)
hd = Note('^D', 74, 17, pulse_ms=40)
he = Note('^E', 76, 5, pulse_ms=40)
hf = Note('^F', 77, 18, pulse_ms=18)


def full_center_text(text, clear=True):
    oled.fill(0)
    oled.rect(0, 0, oled_width, oled_height, 1)
    oled.text(text, center(text), (oled_height - font_px)//2)
    oled.show()


class Chimes(object):
  
  def __init__(self):
    self.intro()
    self.files = [('(Random Play)',self.random_play)] + [fn for fn in os.listdir() if fn.endswith('.mid')] + [('(Exit)',self.exit)]
    self.selected = 0
    self.state = State.SELECT
    self.test()
#    from rotary_irq_esp import RotaryIRQ
#    RotaryIRQ(pin_num_clk=16, pin_num_dt=17, pin_num_sw=5, min_val=0, max_val=10, reverse=False, range_mode=RotaryIRQ.RANGE_WRAP, rotary_callback=lambda x: print('v:', x), sw_callback=lambda: print('s:'))
    tim = machine.Timer(-1)
    tim.init(period=200, mode=machine.Timer.PERIODIC, callback=lambda t:self.check_touch())
    
    
  def random_play(self):
    print('random_play')
    
    
  def exit(self):
    print('exit')
    
    
  def test(self):
    print('self test...')
    for note in Note.ALL:
      note.play()
      time.sleep(.4)
    
  def check_touch(self):
    #print(touch_left.read(), touch_middle.read(), touch_right.read())
    if touch_left.read() < 160: return self.button_press('left')
    if touch_middle.read() < 120: return self.button_press('middle')
    if touch_right.read() < 150: return self.button_press('right')

  
  def show_select(self):
    oled.fill(0)
    ps = page_size
    page = self.selected // page_size
    for i in range(page*page_size, min(len(self.files), (page+1)*page_size)):
      fn = self.files[i]
      display_name = fn[:-4] if isinstance(fn, str) else fn[0]
      oled.text(('>' if self.selected==i else ' ') + display_name, 0, (i-page*page_size)*font_px)
    oled.show()
  
  
  def intro(self):
    oled.fill(0)
    oled.rect(0, 0, oled_width, oled_height, 1)
    full_center_text('Xmas Chimes', clear=False)
  
    
  def show_chime(self, name, note):
    oled.fill(0)
    oled.text(name, center(name), 4)
    oled.text(note, center(note), 14)
    oled.text('pause', 0, 24)
    oled.text('exit', 96, 24)
    oled.show()
  
  
  def play(self, fn, callback=None):
    print('playing', fn)
    display_name = fn[:-4]
    self.state = State.PLAY

    self.show_chime(display_name, 'Loading...')

    gc.collect()
    mid = mido.MidiFile(fn)
    gc.collect()

    started_at = time.time()
    for msg in mid.play():
      if msg.type=='note_on':
        note = Note.midi_note.get(msg.note)
        if note:
          print(note)
          self.show_chime(display_name, note.name)
          note.play()
    
    time.sleep(2)
    if callback: callback()
    

  def select(self):
    print('select')
    self.state = State.SELECT
    self.show_select()
    

  def button_press(self, p):
    if self.state == State.SELECT: self.button_press_SELECT(p)
    elif self.state == State.PLAY: self.button_press_PLAY(p)
    
  def button_press_SELECT(self, p):
    print('button_press_SELECT', p)
    if p=='left':
      self.selected = self.selected-1 if self.selected>0 else len(self.files)-1
      self.show_select()
    elif p=='right':
      self.selected = (self.selected+1) % len(self.files)
      self.show_select()
    elif p=='middle':
      fn = self.files[self.selected]
      if isinstance(fn, str):
        self.play(fn, callback=self.select)
      else:
        fn[1]()
    

  def button_press_PLAY(self, p):
    print('button_press_PLAY', p)

  def run(self):
    self.select()
#    time.sleep(1)
#    self.play(self.files[1], callback=self.select)



chimes = Chimes()

#while True:
#  print(touch_middle.read())

# memory failues common
gc.collect()
print('gc.mem_free()', gc.mem_free())
try:
  import mido
except MemoryError as e:
  print(e)
  full_center_text('OOM')
  time.sleep(3)
  machine.reset()
gc.collect()
print('gc.mem_free()', gc.mem_free())

#touch_left_pin.irq(trigger=Pin.IRQ_RISING, handler=chimes.button_press)
#touch_middle_pin.irq(trigger=Pin.IRQ_RISING, handler=chimes.button_press)
#touch_right_pin.irq(trigger=Pin.IRQ_RISING, handler=chimes.button_press)

chimes.run()

