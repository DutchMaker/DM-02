var emulator = { 
  max_iterations: 10000, // Max iterations in main loop before UI update is called.
  main_address: 0,
  offset: 0,
  last_instruction: 0,
  state: {
    registers: {
      a: 0,
      b: 0,
      c: 0,
      h: 0,
      l: 0,
      ir: 0
    },
    sp: 0,
    pc: 0,
    flags: {
      z: 0,
      c: 0,
      o: 0,
      n: 0,
      clear: function() {
        emulator.state.flags.z = emulator.state.flags.c = emulator.state.flags.o = emulator.state.flags.n = 0;
      }
    },
    memory: {
      data: [ ],
      get: function(address) { },
      set: function(address, data) { }
    },
    halt: false,
    single_step: false,
    running: false
  },
  ui: {
    objects: {
      a: { },
      b: { },
      c: { },
      h: { },
      l: { },
      ir: { },
      fn: { },
      fz: { },
      fo: { },
      fc: { },
      sp: { },
      pc: { },
      textdisplay: { 
        obj: { },
        data: "",
        dirty: false,
        print: function(str) { }
      },
      videodisplay: { }
    },
    prev_highlighted: 0,
    init: function() { },
    update: function() { }
  },
  emulate: function() { },

  /*
  * Main loop.
  **/
  main: function()
  {
    if (!emulator.state.single_step) {
      var i = 0;
      while (i++ < emulator.max_iterations && emulator.running) {
        // We limit the amount of iterations we do with this loop to prevent blocking the event thread.
        // This allows us to maximize the speed the emulator (setTimeout can't go faster than 1 ms.)
        emulator.emulate();
      }

      emulator.ui.update();
    }

    if (emulator.running) {
      setTimeout(emulator.main, 1);
    }
  },

  /*
  * Initialize the emulator.
  **/
  init: function() 
  { 
    emulator.main_address = (emulator.state.memory.get(1 + emulator.offset) << 8) + emulator.state.memory.get(2 + emulator.offset);
    emulator.state.pc = emulator.main_address;

    document.getElementById("iterations_per_update").value = emulator.max_iterations;

    emulator.disassemble();
    emulator.ui.init();
  },

  /*
  * Load program code from a local file.
  **/
  load_fromdisk: function()
  {
    var file_selector = document.getElementById("program_file");
    
    file_selector.onchange = function() {
      if (file_selector.files.length == 0) {
        return;
      }

      var reader = new FileReader();
      reader.addEventListener("load", function(e) {
        var bytes = new Uint8Array(e.target.result);
        emulator.load_program_binary(bytes);
      });

      reader.readAsArrayBuffer(file_selector.files[0]);
    };

    file_selector.click();
  },
  
  load_fromserver: function()
  {
    var file = "programs/" + document.getElementById("program_server").value;

    if (file == "programs/") {
      return;
    }

    var req = new XMLHttpRequest();
    req.open("GET", file, true);
    req.responseType = "arraybuffer";

    req.onload = function (oEvent) {
      if (req.response) {
        var bytes = new Uint8Array(req.response);
        emulator.load_program_binary(bytes);
      }
    };

    req.send(null);
  },

  load_program_binary: function(bytes)
  {
    emulator.state.memory.data = new Array(0xFF00);

    for (var i = 0; i < bytes.length; i++) {
      emulator.state.memory.data[i] = bytes[i];
    }

    if (emulator.state.memory.get(0) == 0) {
      emulator.state.memory.data[0] = 0xC3;  // Add JMP to start of RAM.
      emulator.state.memory.data[1] = 0x40;
      emulator.state.memory.data[2] = 0x00;
      emulator.offset = 0x4000;
    }

    emulator.last_instruction = bytes.length;
    for (var i = emulator.last_instruction; i < 0xFF00; i++) {
      emulator.state.memory.data[i] = 0;
    }

    emulator.init();
  },

  /*
  * Disassemble the program code in memory and display it.
  **/
  disassemble: function()
  {
    var assembly = "";
    
    if (emulator.offset == 0) {
       // Display bootloader code from ROM.
      assembly += "$0000:&nbsp;";
    
      for (var i = 0; i < 16; i++)
      {
        assembly += emulator.state.memory.get(i).toHex() + "&nbsp;";
  
        if ((i + 1) % 10 == 0)
        {
          assembly += "<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
        }
      }
    }
    
    if (emulator.offset > 0) {
      // Display bootloader code (RAM).
      assembly += "<br>" + emulator.offset.toHex(4) + ":&nbsp;";
      for (var i = emulator.offset; i < 16 + emulator.offset; i++)
      {
        assembly += emulator.state.memory.get(i).toHex() + "&nbsp;";

        if ((i + 1) % 10 == 0)
        {
          assembly += "<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
        }
      }
    }

    assembly += "<br />";
    assembly += (emulator.offset + 0x10).toHex(4) + ":&nbsp;";

    // First display the predefined data.
    for (var i = emulator.offset + 0x10; i < emulator.main_address; i++)
    {
      assembly += emulator.state.memory.get(i).toHex() + "&nbsp;";

      if ((i - (emulator.offset + 0x10) + 1) % 10 == 0)
      {
        assembly += "<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
      }
    }
    
    assembly += "<br />";

    // Now disassemble the machine code.
    for (var i = emulator.main_address; i < emulator.last_instruction; i++)
    {
      var opcode = emulator.state.memory.get(i);
      var instruction = emulator.instructions.findByOpcode(opcode);

      assembly += "<a name='code_" + i + "'>" + i.toHex(4) + ":&nbsp;" + opcode.toHex() + "&nbsp;&nbsp;&nbsp;&nbsp;;&nbsp;" + instruction[2] + "</a><br />";

      if (instruction[1] > 1)
      {
        for (var d = i + 1; d < i + instruction[1]; d++)
        {
          var data = emulator.state.memory.get(d);
          assembly += "<a name='code_" + d + "'>" + d.toHex(4) + ":&nbsp;" + data.toHex() + "</a><br />";
        }

        i += instruction[1] - 1;
      }
    }

    document.getElementById("assembly").innerHTML = assembly;
  },

  handle_output: function(address, data)
  {
    switch (address)
    {
      case 0xFF00:
        emulator.ui.objects.textdisplay.data += String.fromCharCode(data);
        emulator.ui.objects.textdisplay.dirty = true;
      case 0xFF01:
      case 0xFF02:
        emulator.ui.objects.videodisplay.load(address, data);
        break;
    }
  },

  /*
  * Halt the processor.
  **/
  halt: function() 
  { 
    emulator.ui.update();

    emulator.state.halt = !emulator.state.halt;
    document.getElementById("button_halt").innerText = emulator.state.halt ? "Continue" : "Halt";
  },

  /*
  * Step by one instruction.
  **/
  step: function()
  {
    emulator.emulate();
    emulator.ui.update();
  },

  /*
  * Stop the emulator.
  **/
  start_stop: function()
  {
    if (emulator.running) {     
      document.getElementById("button_startstop").innerText = "Restart";
      document.getElementById("button_halt").innerText = "Halt";
      document.getElementById("button_halt").disabled = true;

      emulator.running = false;
      emulator.state.halt = false;
    }
    else {
      document.getElementById("button_startstop").innerText = "Stop";
      document.getElementById("button_halt").disabled = false;
      emulator.running = true;

      emulator.reset();
      emulator.main();
    }
  },

  reset: function()
  {
    emulator.state.pc = emulator.main_address;
    emulator.ui.prev_highlighted = 0;
    emulator.ui.objects.textdisplay.data = "";
    emulator.ui.objects.textdisplay.dirty = true;

    emulator.state.registers.a = 0;
    emulator.state.registers.b = 0;
    emulator.state.registers.c = 0;
    emulator.state.registers.h = 0;
    emulator.state.registers.l = 0;
    emulator.state.registers.ir = 0;
    emulator.state.sp = 0;
    emulator.state.flags.clear();

    emulator.ui.objects.videodisplay.reset();

    emulator.ui.update();
  },
};

emulator.state.memory.get = function(address) 
{ 
  return (address >= 0xFF00)
    ? emulator.handle_input(address)
    : emulator.state.memory.data[address];
};

emulator.state.memory.set = function(address, data) 
{
  if (address >= 0xFF00) {
    emulator.handle_output(address, data);
    return;
  }

  emulator.state.memory.data[address] = data;
};

emulator.ui.init = function()
{
  emulator.ui.objects.a = document.getElementById("ra");
  emulator.ui.objects.b = document.getElementById("rb");
  emulator.ui.objects.c = document.getElementById("rc");
  emulator.ui.objects.h = document.getElementById("rh");
  emulator.ui.objects.l = document.getElementById("rl");
  emulator.ui.objects.ir = document.getElementById("rir");

  emulator.ui.objects.sp = document.getElementById("sp");
  emulator.ui.objects.pc = document.getElementById("pc");

  emulator.ui.objects.fn = document.getElementById("fn");
  emulator.ui.objects.fz = document.getElementById("fz");
  emulator.ui.objects.fo = document.getElementById("fo");
  emulator.ui.objects.fc = document.getElementById("fc");

  emulator.ui.objects.textdisplay.obj = document.getElementById("textdisplay");
  
  emulator.ui.objects.videodisplay.init();

  emulator.ui.update();
};

emulator.ui.update = function()
{
  if (!emulator.running) {
    return;
  }

  // Highlight the specified address in the disassembled code.
  if (emulator.state.pc != emulator.ui.prev_highlighted)
  {
    var address = emulator.state.pc;
    var cur = document.getElementsByName("code_" + address)[0];
    var sel = document.getElementsByName("code_" + (address - 15))[0];
    var prev = document.getElementsByClassName("selected_address")[0];

    if (cur) {
      if (prev) {
        prev.className = "";
      }

      cur.className = "selected_address";

      if (sel) {
        sel.scrollIntoView();
      }
      else {
        cur.scrollIntoView();
        //document.getElementById("assembly").scrollTop = 0;
      }
    }

    emulator.ui.prev_highlighted = address;
  }

  emulator.ui.objects.a.innerText = emulator.state.registers.a.toHex();
  emulator.ui.objects.b.innerText = emulator.state.registers.b.toHex();
  emulator.ui.objects.c.innerText = emulator.state.registers.c.toHex();
  emulator.ui.objects.h.innerText = emulator.state.registers.h.toHex();
  emulator.ui.objects.l.innerText = emulator.state.registers.l.toHex();
  emulator.ui.objects.ir.innerText = emulator.state.registers.ir.toHex();

  emulator.ui.objects.sp.innerText = emulator.state.sp.toHex(4);
  emulator.ui.objects.pc.innerText = emulator.state.pc.toHex(4);

  emulator.ui.objects.fn.className = "value v" + emulator.state.flags.n;
  emulator.ui.objects.fz.className = "value v" + emulator.state.flags.z;
  emulator.ui.objects.fo.className = "value v" + emulator.state.flags.o;
  emulator.ui.objects.fc.className = "value v" + emulator.state.flags.c;

  if (emulator.ui.objects.textdisplay.dirty) {
    emulator.ui.objects.textdisplay.obj.innerText = emulator.ui.objects.textdisplay.data;
    emulator.ui.objects.textdisplay.obj.scrollTop = emulator.ui.objects.textdisplay.obj.scrollHeight;
    emulator.ui.objects.textdisplay.dirty = false;
  }

  emulator.ui.objects.videodisplay.update();
}

emulator.ui.objects.textdisplay.print = function(str)
{
  emulator.ui.objects.textdisplay.data += str;
  emulator.ui.objects.textdisplay.dirty = true;
}

Number.prototype.toHex = function(len)
{
  var l = len > 0 ? len : 2;
  return "$" + this.toString(16).toUpperCase().padStart(l, '0');
}

// Attach events to DOM objects.
document.getElementById("button_halt").addEventListener("click", emulator.halt);
document.getElementById("button_step").addEventListener("click", emulator.step);
document.getElementById("button_startstop").addEventListener("click", emulator.start_stop);
document.getElementById("button_load").addEventListener("click", emulator.load_fromdisk);
document.getElementById("program_server").addEventListener("change", emulator.load_fromserver);
document.getElementById("iterations_per_update").addEventListener("change", function() { emulator.max_iterations = parseInt(this.value) });

document.getElementById("single_step").addEventListener("change", function() { 
  emulator.state.single_step = !emulator.state.single_step; 
  document.getElementById("button_step").disabled = !emulator.state.single_step; 
  document.getElementById("iterations_per_update").disabled = emulator.state.single_step;
});

// Load additional JavaScript files.
document.write('<script type="text/javascript" src="js/videodisplay.js"></script>');
document.write('<script type="text/javascript" src="js/instructions.js"></script>');
document.write('<script type="text/javascript" src="js/instructions_logic.js"></script>');
document.write('<script type="text/javascript" src="js/example_program.js"></script>');

document.addEventListener("DOMContentLoaded", emulator.init, true);