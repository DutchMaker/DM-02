namespace Emulator
{
    public class CpuModules
    {
        public Register A { get; } = new Register();

        public Register B { get; } = new Register();

        public Register C { get; } = new Register();
        
        public Register H { get; } = new Register();
        
        public Register L { get; } = new Register();
        
        public Register IR { get; } = new Register();
        
        public FlagsRegister F { get; } = new FlagsRegister();
        
        public ArithmeticLogicUnit ALU { get; } = new ArithmeticLogicUnit();
        
        public MemoryAccessRegister MAR { get; } = new MemoryAccessRegister();
        
        public Memory MEM { get; } = new Memory();
        
        public ProgramCounter PC { get; } = new ProgramCounter();
        
        public StackPointer STK { get; } = new StackPointer();
        
        public Controller CONTROLLER { get; } = new Controller();
        
        public BusConnections BUS { get; } = new BusConnections();
        
        public Clock CLOCK { get; } = new Clock();

        public CpuModules()
        {
            A.BUS = BUS;
            B.BUS = BUS;
            C.BUS = BUS;
            H.BUS = BUS;
            L.BUS = BUS;
            IR.BUS = BUS;
            F.BUS = BUS;
            ALU.BUS = BUS;
            MAR.BUS = BUS;
            MEM.BUS = BUS;
            PC.BUS = BUS;
            STK.BUS = BUS;
            A.CLOCK = CLOCK;
            B.CLOCK = CLOCK;
            C.CLOCK = CLOCK;
            H.CLOCK = CLOCK;
            L.CLOCK = CLOCK;
            IR.CLOCK = CLOCK;
            F.CLOCK = CLOCK;
            ALU.CLOCK = CLOCK;
            MAR.CLOCK = CLOCK;
            MEM.CLOCK = CLOCK;
            PC.CLOCK = CLOCK;
            STK.CLOCK = CLOCK;
            CONTROLLER.CLOCK = CLOCK;
        }

        public void Tick()
        {
            CLOCK.Tick();
            A.Tick();
            B.Tick();
            C.Tick();
            H.Tick();
            L.Tick();
            IR.Tick();
            F.Tick();
            ALU.Tick();
            MAR.Tick();
            MEM.Tick();
            PC.Tick();
            STK.Tick();
            CONTROLLER.Tick();
        }
    }
}