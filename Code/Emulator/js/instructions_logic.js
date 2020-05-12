/*
* Emulate the current processor state.
**/
emulator.emulate = function() 
{ 
  if (emulator.state.halt) {
    return;
  }

  var opcode = emulator.state.memory.get(emulator.state.pc);
  emulator.state.pc++;

  var data, data_hi, data_lo, address, indirect_address;

  // Get data for immediate instructions.
  switch (opcode)
  {
    case 0x17:	// MOV A,value
    case 0x18:	// MOV B,value
    case 0x19:	// MOV C,value
    case 0x1A:	// MOV H,value
    case 0x1B:	// MOV L,value
    case 0x58:	// ADD value
    case 0x61:	// ADC value
    case 0x6A:	// SUB value
    case 0x73:	// SBC value
    case 0x85:	// AND value
    case 0x8D:	// OR value
    case 0x95:	// XOR value
    case 0x9E:	// NOT value
    case 0xA6:	// SHL value
    case 0xAB:	// SHR value
    case 0xB0:	// ASR value
    case 0xB5:	// ROL value
    case 0xBA:	// ROR value
    case 0xBF:	// CMP value
      data = emulator.state.memory.get(emulator.state.pc++);
      break;
    case 0x1C:	// MOV BC,value
    case 0x1D:	// MOV HL,value
      data_hi = emulator.state.memory.get(emulator.state.pc++);
      data_lo = emulator.state.memory.get(emulator.state.pc++);
      break;
  }

  // Get data for register instructions.
  switch (opcode)
  {
    case 0x05:	// MOV B,A
    case 0x09:	// MOV C,A
    case 0x0D:	// MOV H,A
    case 0x11:	// MOV L,A
    case 0x23:	// MOV address,A
    case 0x2C:	// MOV (address),A
    case 0x36:	// MOV (BC),A
    case 0x39:	// MOV (HL),A
    case 0x43:	// PUSH A
    case 0x53:	// ADD A
    case 0x5C:	// ADC A
    case 0x65:	// SUB A
    case 0x99:	// NOT A
      data = emulator.state.registers.a;
      break;
    case 0x01:	// MOV A,B
    case 0x0A:	// MOV C,B
    case 0x0E:	// MOV H,B
    case 0x12:	// MOV L,B
    case 0x24:	// MOV address,B
    case 0x2D:	// MOV (address),B
    case 0x3A:	// MOV (HL),B
    case 0x44:	// PUSH B
    case 0x54:	// ADD B
    case 0x5D:	// ADC B
    case 0x66:	// SUB B
    case 0x81:	// AND B
    case 0x89:	// OR B
    case 0x91:	// XOR B
    case 0x9A:	// NOT B
    case 0xA2:	// SHL B
    case 0xA7:	// SHR B
    case 0xAC:	// ASR B
    case 0xB1:	// ROL B
    case 0xB6:	// ROR B
    case 0xBB:	// CMP B
      data = emulator.state.registers.b;
      break;
    case 0x02:	// MOV A,C
    case 0x06:	// MOV B,C
    case 0x0F:	// MOV H,C
    case 0x13:	// MOV L,C
    case 0x25:	// MOV address,C
    case 0x2E:	// MOV (address),C
    case 0x3B:	// MOV (HL),C
    case 0x45:	// PUSH C
    case 0x55:	// ADD C
    case 0x5E:	// ADC C
    case 0x67:	// SUB C
    case 0x82:	// AND C
    case 0x8A:	// OR C
    case 0x92:	// XOR C
    case 0x9B:	// NOT C
    case 0xA3:	// SHL C
    case 0xA8:	// SHR C
    case 0xAD:	// ASR C
    case 0xB2:	// ROL C
    case 0xB7:	// ROR C
    case 0xBC:	// CMP C
      data = emulator.state.registers.c;
      break;
    case 0x03:	// MOV A,H
    case 0x07:	// MOV B,H
    case 0x0B:	// MOV C,H
    case 0x14:	// MOV L,H
    case 0x37:	// MOV (BC),H
    case 0x46:	// PUSH H
    case 0x56:	// ADD H
    case 0x5F:	// ADC H
    case 0x68:	// SUB H
    case 0x83:	// AND H
    case 0x8B:	// OR H
    case 0x93:	// XOR H
    case 0x9C:	// NOT H
    case 0xA4:	// SHL H
    case 0xA9:	// SHR H
    case 0xAE:	// ASR H
    case 0xB3:	// ROL H
    case 0xB8:	// ROR H
    case 0xBD:	// CMP H
      data = emulator.state.registers.h;
      break;
    case 0x04:	// MOV A,L
    case 0x08:	// MOV B,L
    case 0x0C:	// MOV C,L
    case 0x10:	// MOV H,L
    case 0x38:	// MOV (BC),L
    case 0x47:	// PUSH L
    case 0x57:	// ADD L
    case 0x60:	// ADC L
    case 0x69:	// SUB L
    case 0x84:	// AND L
    case 0x8C:	// OR L
    case 0x94:	// XOR L
    case 0x9D:	// NOT L
    case 0xA5:	// SHL L
    case 0xAA:	// SHR L
    case 0xAF:	// ASR L
    case 0xB4:	// ROL L
    case 0xB9:	// ROR L
    case 0xBE:	// CMP L
      data = emulator.state.registers.l;
      break;
    case 0x15:	// MOV BC,HL
    case 0x27:	// MOV address,HL
    case 0x49:	// PUSH HL
      data_hi = emulator.state.registers.h;
      data_lo = emulator.state.registers.l;
      break;
    case 0x16:	// MOV HL,BC
    case 0x26:	// MOV address,BC 
    case 0x2F:	// MOV (address),BC
    case 0x48:	// PUSH BC
      data_hi = emulator.state.registers.b;
      data_lo = emulator.state.registers.c;
      break;
  }

  // Get data and address for direct addressing instructions.
  switch (opcode)
  {
    case 0x23:	// MOV address,A
    case 0x24:	// MOV address,B
    case 0x25:	// MOV address,C
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      break;
    case 0x1E:	// MOV A,address
    case 0x1F:	// MOV B,address
    case 0x20:	// MOV C,address
    case 0x42:	// SP address
    case 0x59:	// ADD address
    case 0x62:	// ADC address
    case 0x6B:	// SUB address
    case 0x74:	// SBC address
    case 0x86:	// AND address
    case 0x8E:	// OR address
    case 0x96:	// XOR address
    case 0x9F:	// NOT address
    case 0xC0:	// CMP address
    case 0xC3:	// JMP address
    case 0xC4:	// JC address
    case 0xC5:	// JZ address
    case 0xC6:	// JN address
    case 0xC7:	// JO address
    case 0xC8:	// JNC address
    case 0xC9:	// JNZ address
    case 0xCA:	// JP address
    case 0xCB:	// JNO address
    case 0xCC:	// CALL address
    case 0xCD:	// CC address
    case 0xCE:	// CZ address
    case 0xCF:	// CN address
    case 0xD0:	// CO address
    case 0xD1:	// CNC address
    case 0xD2:	// CNZ address
    case 0xD3:	// CP address
    case 0xD4:	// CNO address
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      data = emulator.state.memory.get(address);
      break;
    case 0x26:	// MOV address,BC 
    case 0x27:	// MOV address,HL
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      break;
    case 0x21:	// MOV BC,address
    case 0x22:	// MOV HL,address
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      data_hi = emulator.state.memory.get(address);
      data_lo = emulator.state.memory.get(address + 1);
      break;
  }

  // Get data for indirect addressing instructions.
  switch (opcode)
  {
    case 0x2C:	// MOV (address),A
    case 0x2D:	// MOV (address),B
    case 0x2E:	// MOV (address),C
    case 0x2F:	// MOV (address),BC
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      indirect_address = (emulator.state.memory.get(address) << 8) + emulator.state.memory.get(address + 1);
      break;
    case 0x28:	// MOV A,(address)
    case 0x29:	// MOV B,(address)
    case 0x2A:	// MOV C,(address)
    case 0x2B:	// MOV BC,(address)
    case 0x5A:	// ADD (address)
    case 0x63:	// ADC (address)
    case 0x6C:	// SUB (address)
    case 0x75:	// SBC (address)
    case 0x87:	// AND (address)
    case 0x8F:	// OR (address)
    case 0x97:	// XOR (address)
    case 0xA0:	// NOT (address)
    case 0xC1:	// CMP (address)
      address = (emulator.state.memory.get(emulator.state.pc++) << 8) + emulator.state.memory.get(emulator.state.pc++);
      indirect_address = (emulator.state.memory.get(address) << 8) + emulator.state.memory.get(address + 1);
      data = emulator.state.memory.get(indirect_address);
      break;
  }

  // Get data for indirect register BC addressing.
  switch (opcode)
  {
    case 0x36:	// MOV (BC),A
    case 0x37:	// MOV (BC),H
    case 0x38:	// MOV (BC),L
      address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
      break;
    case 0x30:	// MOV A,(BC)
    case 0x31:	// MOV H,(BC)
    case 0x32:	// MOV L,(BC)
      address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
      data = emulator.state.memory.get(address);
      break;
    case 0x41:	// MOV (BC),HL
      address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
      break;
    case 0x3C:	// MOV BC,(BC)
    case 0x3E:	// MOV HL,(BC)
      address = indirect_address = (emulator.state.registers.b << 8) + emulator.state.registers.c;
      data_hi = emulator.state.memory.get(address);
      data_lo = emulator.state.memory.get(address + 1);
      break;
  }

  // Get data for indirect register HL addressing.
  switch (opcode)
  {
    case 0x40:	// MOV (HL),BC
    case 0x39:	// MOV (HL),A
    case 0x3A:	// MOV (HL),B
    case 0x3B:	// MOV (HL),C
      address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
      break;
    case 0x3D:	// MOV BC,(HL)
    case 0x3F:	// MOV HL,(HL)
      address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
      data_hi = emulator.state.memory.get(address);
      data_lo = emulator.state.memory.get(address + 1);
      break;
    case 0x33:	// MOV A,(HL)
    case 0x34:	// MOV B,(HL)
    case 0x35:	// MOV C,(HL)
    case 0x5B:	// ADD (HL)
    case 0x64:	// ADC (HL)
    case 0x6D:	// SUB (HL)
    case 0x76:	// SBC (HL)
    case 0x88:	// AND (HL)
    case 0x90:	// OR (HL)
    case 0x98:	// XOR (HL)
    case 0xA1:	// NOT (HL)
    case 0xC2:	// CMP (HL)
      address = indirect_address = (emulator.state.registers.h << 8) + emulator.state.registers.l;
      data = emulator.state.memory.get(address);
      break;
  }

  var flag_update = false;

  // Instructions that affect flags.
  switch (opcode)
  {
    case 0x53:	// ADD A
    case 0x54:	// ADD B
    case 0x55:	// ADD C
    case 0x56:	// ADD H
    case 0x57:	// ADD L
    case 0x58:	// ADD value
    case 0x59:	// ADD address
    case 0x5A:	// ADD (address)
    case 0x5B:	// ADD (HL)
    case 0x5C:	// ADC A
    case 0x5D:	// ADC B
    case 0x5E:	// ADC C
    case 0x5F:	// ADC H
    case 0x60:	// ADC L
    case 0x61:	// ADC value
    case 0x62:	// ADC address
    case 0x63:	// ADC (address)
    case 0x64:	// ADC (HL)
    case 0x65:	// SUB A
    case 0x66:	// SUB B
    case 0x67:	// SUB C
    case 0x68:	// SUB H
    case 0x69:	// SUB L
    case 0x6A:	// SUB value
    case 0x6B:	// SUB address
    case 0x6C:	// SUB (address)
    case 0x6D:	// SUB (HL)
    case 0x6E:	// SBC A
    case 0x6F:	// SBC B
    case 0x70:	// SBC C
    case 0x71:	// SBC H
    case 0x72:	// SBC L
    case 0x73:	// SBC value
    case 0x74:	// SBC address
    case 0x75:	// SBC (address)
    case 0x76:	// SBC (HL)
    case 0x77:	// INC A
    case 0x7C:	// DEC A
    case 0x81:	// AND B
    case 0x82:	// AND C
    case 0x83:	// AND H
    case 0x84:	// AND L
    case 0x85:	// AND value
    case 0x86:	// AND address
    case 0x87:	// AND (address)
    case 0x88:	// AND (HL)
    case 0x89:	// OR B
    case 0x8A:	// OR C
    case 0x8B:	// OR H
    case 0x8C:	// OR L
    case 0x8D:	// OR value
    case 0x8E:	// OR address
    case 0x8F:	// OR (address)
    case 0x90:	// OR (HL)
    case 0x91:	// XOR B
    case 0x92:	// XOR C
    case 0x93:	// XOR H
    case 0x94:	// XOR L
    case 0x95:	// XOR value
    case 0x96:	// XOR address
    case 0x97:	// XOR (address)
    case 0x98:	// XOR (HL)
    case 0x99:	// NOT A
    case 0x9A:	// NOT B
    case 0x9B:	// NOT C
    case 0x9C:	// NOT H
    case 0x9D:	// NOT L
    case 0x9E:	// NOT value
    case 0x9F:	// NOT address
    case 0xA0:	// NOT (address)
    case 0xA1:	// NOT (HL)
    case 0xA2:	// SHL B
    case 0xA3:	// SHL C
    case 0xA4:	// SHL H
    case 0xA5:	// SHL L
    case 0xA6:	// SHL value
    case 0xA7:	// SHR B
    case 0xA8:	// SHR C
    case 0xA9:	// SHR H
    case 0xAA:	// SHR L
    case 0xAB:	// SHR value
    case 0xAC:	// ASR B
    case 0xAD:	// ASR C
    case 0xAE:	// ASR H
    case 0xAF:	// ASR L
    case 0xB0:	// ASR value
    case 0xB1:	// ROL B
    case 0xB2:	// ROL C
    case 0xB3:	// ROL H
    case 0xB4:	// ROL L
    case 0xB5:	// ROL value
    case 0xB6:	// ROR B
    case 0xB7:	// ROR C
    case 0xB8:	// ROR H
    case 0xB9:	// ROR L
    case 0xBA:	// ROR value
      flag_update = true;
      break;
  }

  // Update the emulator state.
  switch (opcode)
  {
    case 0x00:	// NOP
      break;
    case 0x01:	// MOV A,B
    case 0x02:	// MOV A,C
    case 0x03:	// MOV A,H
    case 0x04:	// MOV A,L
    case 0x17:	// MOV A,value
    case 0x1E:	// MOV A,address
    case 0x28:	// MOV A,(address)
    case 0x30:	// MOV A,(BC)
    case 0x33:	// MOV A,(HL)
      emulator.state.registers.a = data;
      break;
    case 0x05:	// MOV B,A
    case 0x06:	// MOV B,C
    case 0x07:	// MOV B,H
    case 0x08:	// MOV B,L
    case 0x18:	// MOV B,value
    case 0x1F:	// MOV B,address
    case 0x29:	// MOV B,(address)
    case 0x34:	// MOV B,(HL)
      emulator.state.registers.b = data;
      break;
    case 0x09:	// MOV C,A
    case 0x0A:	// MOV C,B
    case 0x0B:	// MOV C,H
    case 0x0C:	// MOV C,L
    case 0x19:	// MOV C,value
    case 0x20:	// MOV C,address
    case 0x2A:	// MOV C,(address)
    case 0x35:	// MOV C,(HL)
      emulator.state.registers.c = data;
      break;
    case 0x0D:	// MOV H,A
    case 0x0E:	// MOV H,B
    case 0x0F:	// MOV H,C
    case 0x10:	// MOV H,L
    case 0x1A:	// MOV H,value
    case 0x31:	// MOV H,(BC)
      emulator.state.registers.h = data;
      break;
    case 0x11:	// MOV L,A
    case 0x12:	// MOV L,B
    case 0x13:	// MOV L,C
    case 0x14:	// MOV L,H
    case 0x1B:	// MOV L,value
    case 0x32:	// MOV L,(BC)
      emulator.state.registers.l = data;
      break;
    case 0x15:	// MOV BC,HL
    case 0x1C:	// MOV BC,value
    case 0x21:	// MOV BC,address
    case 0x2B:	// MOV BC,(address)
    case 0x3C:	// MOV BC,(BC)
    case 0x3D:	// MOV BC,(HL)
      emulator.state.registers.b = data_hi;
      emulator.state.registers.c = data_lo;
      break;
    case 0x16:	// MOV HL,BC
    case 0x1D:	// MOV HL,value
    case 0x22:	// MOV HL,address
    case 0x3E:	// MOV HL,(BC)
    case 0x3F:	// MOV HL,(HL)
      emulator.state.registers.h = data_hi;
      emulator.state.registers.l = data_lo;
      break;
    case 0x23:	// MOV address,A
    case 0x24:	// MOV address,B
    case 0x25:	// MOV address,C
      emulator.state.memory.set(address, data);
      break;
    case 0x2C:	// MOV (address),A
    case 0x2D:	// MOV (address),B
    case 0x2E:	// MOV (address),C
    case 0x36:	// MOV (BC),A
    case 0x37:	// MOV (BC),H
    case 0x38:	// MOV (BC),L
    case 0x39:	// MOV (HL),A
    case 0x3A:	// MOV (HL),B
    case 0x3B:	// MOV (HL),C
      emulator.state.memory.set(indirect_address, data);
      break;
    case 0x26:	// MOV address,BC
    case 0x27:	// MOV address,HL
    case 0x2F:	// MOV (address),BC
      emulator.state.memory.set(address, data_hi);
      emulator.state.memory.set(address + 1, data_lo);
      break;
    case 0x40:	// MOV (HL),BC
    case 0x41:	// MOV (BC),HL
      emulator.state.memory.set(indirect_address, data_hi);
      emulator.state.memory.set(indirect_address + 1, data_lo);
      break;
    case 0x42:	// SP address
      emulator.state.sp = address;
      break;
    case 0x43:	// PUSH A
    case 0x44:	// PUSH B
    case 0x45:	// PUSH C
    case 0x46:	// PUSH H
    case 0x47:	// PUSH L
      emulator.state.memory.set(emulator.state.sp--, data);
      break;
    case 0x48:	// PUSH BC
    case 0x49:	// PUSH HL
      emulator.state.memory.set(emulator.state.sp--, data_hi);
      emulator.state.memory.set(emulator.state.sp--, data_lo);
      break;
    case 0x4A:	// PUSH F
      var byte = emulator.state.flags.c << 3 | emulator.state.flags.z << 2 | emulator.state.flags.o << 1 | emulator.state.flags.n;
      emulator.state.memory.set(emulator.state.sp--, byte);
      break;
    case 0x4B:	// POP A
      emulator.state.registers.a = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x4C:	// POP B
      emulator.state.registers.b = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x4D:	// POP C
      emulator.state.registers.c = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x4E:	// POP H
      emulator.state.registers.h = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x4F:	// POP L
      emulator.state.registers.l = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x50:	// POP BC
      emulator.state.registers.c = emulator.state.memory.get(emulator.state.sp++);
      emulator.state.registers.b = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x51:	// POP HL
      emulator.state.registers.l = emulator.state.memory.get(emulator.state.sp++);
      emulator.state.registers.h = emulator.state.memory.get(emulator.state.sp++);
      break;
    case 0x52:	// POP F
      var byte = emulator.state.memory.get(emulator.state.sp++);
      emulator.state.flags.c = byte & (1 << 3) / 8;
      emulator.state.flags.z = byte & (1 << 2) / 4;
      emulator.state.flags.o = byte & (1 << 1) / 2;
      emulator.state.flags.n = byte & 1;
      break;
    case 0x53:	// ADD A
    case 0x54:	// ADD B
    case 0x55:	// ADD C
    case 0x56:	// ADD H
    case 0x57:	// ADD L
    case 0x58:	// ADD value
    case 0x59:	// ADD address
    case 0x5A:	// ADD (address)
    case 0x5B:	// ADD (HL)
      emulator.state.registers.a += data;
      break;
    case 0x5C:	// ADC A
    case 0x5D:	// ADC B
    case 0x5E:	// ADC C
    case 0x5F:	// ADC H
    case 0x60:	// ADC L
    case 0x61:	// ADC value
    case 0x62:	// ADC address
    case 0x63:	// ADC (address)
    case 0x64:	// ADC (HL)
      emulator.state.registers.a += data + emulator.state.flags.c;
      break;
    case 0x65:	// SUB A
    case 0x66:	// SUB B
    case 0x67:	// SUB C
    case 0x68:	// SUB H
    case 0x69:	// SUB L
    case 0x6A:	// SUB value
    case 0x6B:	// SUB address
    case 0x6C:	// SUB (address)
    case 0x6D:	// SUB (HL)
      emulator.state.registers.a -= data;
      break;
    case 0x6E:	// SBC A
    case 0x6F:	// SBC B
    case 0x70:	// SBC C
    case 0x71:	// SBC H
    case 0x72:	// SBC L
    case 0x73:	// SBC value
    case 0x74:	// SBC address
    case 0x75:	// SBC (address)
    case 0x76:	// SBC (HL)
      emulator.state.registers.a -= (data + emulator.state.flags.c);
      break;
    case 0x77:	// INC A
      emulator.state.registers.a++;
      break;
    case 0x78:	// INC B
      emulator.state.flags.clear();
      if (++emulator.state.registers.b > 255) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 1;
        emulator.state.registers.b = 0;
      }
      break;
    case 0x79:	// INC C
      emulator.state.flags.clear();
      if (++emulator.state.registers.c > 255) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 1;
        emulator.state.registers.c = 0;
      }
      break;
    case 0x7A:	// INC H
      emulator.state.flags.clear();
      if (++emulator.state.registers.h > 255) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 1;
        emulator.state.registers.h = 0;
      }
      break;
    case 0x7B:	// INC L
      emulator.state.flags.clear();
      if (++emulator.state.registers.l > 255) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 1;
        emulator.state.registers.l = 0;
      }
      break;
    case 0x7C:	// DEC A
      emulator.state.registers.a--;
      break;
    case 0x7D:	// DEC B
      emulator.state.flags.clear();
      if (--emulator.state.registers.b < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.n = 1;
        emulator.state.registers.b = 255;
      }
      break;
    case 0x7E:	// DEC C
      emulator.state.flags.clear();
      if (--emulator.state.registers.c < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.n = 1;
        emulator.state.registers.c = 255;
      }
      break;
    case 0x7F:	// DEC H
      emulator.state.flags.clear();
      if (--emulator.state.registers.h < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.n = 1;
        emulator.state.registers.h = 255;
      }
      break;
    case 0x80:	// DEC L
      emulator.state.flags.clear();
      if (--emulator.state.registers.l < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.n = 1;
        emulator.state.registers.l = 255;
      }
      break;
    case 0x81:	// AND B
    case 0x82:	// AND C
    case 0x83:	// AND H
    case 0x84:	// AND L
    case 0x85:	// AND value
    case 0x86:	// AND address
    case 0x87:	// AND (address)
    case 0x88:	// AND (HL)
      emulator.state.registers.a = emulator.state.registers.a & data;
      break;
    case 0x89:	// OR B
    case 0x8A:	// OR C
    case 0x8B:	// OR H
    case 0x8C:	// OR L
    case 0x8D:	// OR value
    case 0x8E:	// OR address
    case 0x8F:	// OR (address)
    case 0x90:	// OR (HL)
      emulator.state.registers.a = emulator.state.registers.a | data;
      break;
    case 0x91:	// XOR B
    case 0x92:	// XOR C
    case 0x93:	// XOR H
    case 0x94:	// XOR L
    case 0x95:	// XOR value
    case 0x96:	// XOR address
    case 0x97:	// XOR (address)
    case 0x98:	// XOR (HL)
      emulator.state.registers.a = emulator.state.registers.a ^ data;
      break;
    case 0x99:	// NOT A
    case 0x9A:	// NOT B
    case 0x9B:	// NOT C
    case 0x9C:	// NOT H
    case 0x9D:	// NOT L
    case 0x9E:	// NOT value
    case 0x9F:	// NOT address
    case 0xA0:	// NOT (address)
    case 0xA1:	// NOT (HL)
      emulator.state.registers.a = ~data;
      break;
    case 0xA2:	// SHL B
    case 0xA3:	// SHL C
    case 0xA4:	// SHL H
    case 0xA5:	// SHL L
    case 0xA6:	// SHL value
      emulator.state.registers.a = emulator.state.registers.a << data;
      break;
    case 0xA7:	// SHR B
    case 0xA8:	// SHR C
    case 0xA9:	// SHR H
    case 0xAA:	// SHR L
    case 0xAB:	// SHR value
      emulator.state.registers.a = emulator.state.registers.a >> data;
      break;
    case 0xAC:	// ASR B
    case 0xAD:	// ASR C
    case 0xAE:	// ASR H
    case 0xAF:	// ASR L
    case 0xB0:	// ASR value
      var a = emulator.state.registers.a;
      var msb = a & 0x80;
      for (var i=0; i < data; i++) {
        a = a >> 1;
        a |= msb;
      } 
      emulator.state.registers.a = a;
      break;
    case 0xB1:	// ROL B
    case 0xB2:	// ROL C
    case 0xB3:	// ROL H
    case 0xB4:	// ROL L
    case 0xB5:	// ROL value
      var a = emulator.state.registers.a;
      for (var i=0; i < data; i++) {
        var msb = a & 0x80;
        a = (a << 1) & 0xff;
        a |= msb ? 1 : 0;
      }
      emulator.state.registers.a = a;
      break;
    case 0xB6:	// ROR B
    case 0xB7:	// ROR C
    case 0xB8:	// ROR H
    case 0xB9:	// ROR L
    case 0xBA:	// ROR value
      var a = emulator.state.registers.a;
      for (var i=0; i < data; i++) {
        var lsb = a & 0x1;
        a = a >> 1;
        a |= lsb ? 0x80 : 0;
      }
      emulator.state.registers.a = a;
      break;
    case 0xBB:	// CMP B
    case 0xBC:	// CMP C
    case 0xBD:	// CMP H
    case 0xBE:	// CMP L
    case 0xBF:	// CMP value
    case 0xC0:	// CMP address
    case 0xC1:	// CMP (address)
    case 0xC2:	// CMP (HL)
      emulator.state.flags.clear();
      if (emulator.state.registers.a - data < 0) {
        emulator.state.flags.o = 1;
        emulator.state.flags.c = 1;
        emulator.state.flags.z = 0;
        emulator.state.flags.n = 1;
      }
      else if (emulator.state.registers.a - data == 0) {
        emulator.state.flags.z = 1;
      }
      break;
    case 0xC3:	// JMP address
      emulator.state.pc = address;
      break;
    case 0xC4:	// JC address
      if (emulator.state.flags.c == 1) {
        emulator.state.pc = address;
      }
      break;
    case 0xC5:	// JZ address
      if (emulator.state.flags.z == 1) {
        emulator.state.pc = address;
      }
      break;
    case 0xC6:	// JN address
      if (emulator.state.flags.n == 1) {
        emulator.state.pc = address;
      }
      break;
    case 0xC7:	// JO address
      if (emulator.state.flags.o == 1) {
        emulator.state.pc = address;
      }
      break;
    case 0xC8:	// JNC address
      if (emulator.state.flags.c == 0) {
        emulator.state.pc = address;
      }
      break;
    case 0xC9:	// JNZ address
      if (emulator.state.flags.z == 0) {
        emulator.state.pc = address;
      }
      break;
    case 0xCA:	// JP address
      if (emulator.state.flags.n == 0) {
        emulator.state.pc = address;
      }
      break;
    case 0xCB:	// JNO address
      if (emulator.state.flags.o == 0) {
        emulator.state.pc = address;
      }
      break;
    case 0xCC:	// CALL address
      emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
      emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
      emulator.state.pc = address;
      break;
    case 0xCD:	// CC address
      if (emulator.state.flags.c == 1) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xCE:	// CZ address
      if (emulator.state.flags.z == 1) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xCF:	// CN address
      if (emulator.state.flags.n == 1) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD0:	// CO address
      if (emulator.state.flags.o == 1) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD1:	// CNC address
      if (emulator.state.flags.c == 0) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD2:	// CNZ address
      if (emulator.state.flags.z == 0) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD3:	// CP address
      if (emulator.state.flags.n == 0) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD4:	// CNO address
      if (emulator.state.flags.o == 0) {
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc >> 8);
        emulator.state.memory.set(emulator.state.sp--, emulator.state.pc & 0xFF);
        emulator.state.pc = address;
      }
      break;
    case 0xD5:	// RET
      var lo = emulator.state.memory.get(++emulator.state.sp);
      var hi = emulator.state.memory.get(++emulator.state.sp);
      var addr = (hi << 8) + lo;

      emulator.state.pc = addr;
      break;
    case 0xD6:	// RC
      if (emulator.state.flags.c == 1) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xD7:	// RZ
      if (emulator.state.flags.z == 1) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xD8:	// RN
      if (emulator.state.flags.n == 1) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xD9:	// RO
      if (emulator.state.flags.o == 1) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xDA:	// RNC
      if (emulator.state.flags.c == 0) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xDB:	// RNZ
      if (emulator.state.flags.z == 0) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xDC:	// RP
      if (emulator.state.flags.n == 0) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      }
      break;
    case 0xDD:	// RNO
      if (emulator.state.flags.o == 0) {
        var lo = emulator.state.memory.get(++emulator.state.sp);
        var hi = emulator.state.memory.get(++emulator.state.sp);
        var addr = (hi << 8) + lo;

        emulator.state.pc = addr;
      } 
      break;
    case 0xDE:	// FSET C
      emulator.state.flags.c = 1;
      break;
    case 0xDF:	// FSET Z
      emulator.state.flags.z = 1;
      break;
    case 0xE0:	// FCLR C
      emulator.state.flags.c = 0;
      break;
    case 0xE1:	// FCLR Z
      emulator.state.flags.z = 0;
      break;
    case 0xE2:	// HALT
      emulator.halt();
      break;
    default:
      throw "Unknown opcode: " + opcode.toHex();
  }

  if (flag_update) {
    emulator.state.flags.clear();

    if (emulator.state.registers.a == 0)
    {
      emulator.state.flags.z = 1;
    }

    if (emulator.state.registers.a > 255) {
      emulator.state.flags.o = 1;
      emulator.state.flags.c = 1;
      emulator.state.flags.z = 1;
      emulator.state.registers.a = 0;
    }

    if (emulator.state.registers.a < 0) {
      emulator.state.flags.o = 1;
      emulator.state.flags.c = 1;
      emulator.state.flags.z = 0;
      emulator.state.flags.n = 1;
      emulator.state.registers.a = 255;
    }
  }

  if (emulator.state.pc > 0xFFFF) {
    emulator.start_stop();
  }
};