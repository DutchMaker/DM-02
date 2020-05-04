var emulator = { 

  main_address: 0,
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
    pc: 0x20,
    flags: {
      z: false,
      c: false,
      o: false,
      n: false
    },
    memory: {
      rom: [ ],
      ram: [ ],
      getData: function(address) { }
    },
    halt: false
  },

  main: function() 
  { 
    emulator.init();
  },

  init: function() 
  { 
    emulator.main_address = (emulator.state.memory.rom[1] << 8) + emulator.state.memory.rom[2];
    console.log("Program starts at address " + emulator.main_address.toHex(4));

    emulator.disassemble();
  },

  disassemble: function()
  {
    var assembly = (0x10).toHex(4) + ":&nbsp;";
    
    // First display the predefined data.
    for (var i = 0x10; i < emulator.main_address; i++)
    {
      assembly += emulator.state.memory.rom[i].toHex() + "&nbsp;";

      if ((i - 0x10 + 1) % 10 == 0)
      {
        assembly += "<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;";
      }
    }
    
    assembly += "<br />";

    // Now disassemble the machine code.
    for (var i = emulator.main_address; i < emulator.state.memory.rom.length; i++)
    {
      var opcode = emulator.state.memory.rom[i];
      var instruction = emulator.instructions.findByOpcode(opcode);

      assembly += "<a name='code_" + i + "'>" + i.toHex(4) + ":&nbsp;" + opcode.toHex() + "&nbsp;&nbsp;&nbsp;&nbsp;;&nbsp;" + instruction[2] + "</a><br />";

      if (instruction[1] > 1)
      {
        for (var d = i + 1; d < i + instruction[1]; d++)
        {
          var data = emulator.state.memory.rom[d];
          assembly += "<a name='code_" + d + "'>" + d.toHex(4) + ":&nbsp;" + data.toHex() + "</a><br />";
        }

        i += instruction[1] - 1;
      }
    }

    document.getElementById("assembly").innerHTML = assembly;
  },

  highlight_instruction: function(address)
  {
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
    }
  },

  halt: function() 
  { 
    emulator.state.halt = !emulator.state.halt;
    document.getElementById("button_halt").innerText = emulator.state.halt ? "Continue" : "Halt";
  },

  emulate: function(state) 
  { 
    var opcode = emulator.memory.getData(emulator.state.pc);
  }
}

Number.prototype.toHex = function(len)
{
  var l = len > 0 ? len : 2;

  return "$" + this.toString(16).toUpperCase().padStart(l, '0');
}

document.getElementById("button_halt").addEventListener("click", emulator.halt);

document.getElementById("button_step").addEventListener("click", function() {
  emulator.state.pc++;
  emulator.highlight_instruction(emulator.state.pc);
});

document.write('<script type="text/javascript" src="js/example_program.js"></script>');
document.write('<script type="text/javascript" src="js/instructions.js"></script>');
document.addEventListener("DOMContentLoaded", emulator.main, true);