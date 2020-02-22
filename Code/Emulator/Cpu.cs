namespace Emulator
{
    public class Cpu
    {
        public Register A { get; } = new Register();
        public Register B { get; } = new Register();
        public Register C { get; } = new Register();
        public Register H { get; } = new Register();
        public Register L { get; } = new Register();
        public Register IR { get; } = new Register();
        public FlagsRegister F { get; } = new FlagsRegister();
        public Alu ALU { get; } = new Alu();
        public Mar MAR { get; } = new Mar();
        public Mem MEM { get; } = new Mem();
        public Bus BUS { get; } = new Bus();

        public Cpu()
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
        }

        public void Run()
        {

        }
        
        public void Stop()
        {

        }

        public void Reset()
        {

        }
    }
}