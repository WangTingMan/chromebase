#include <iostream>
#include <base/debug/stack_trace.h>
#include "base/bind.h"
#include <base\callback.h>
#include <chrono>
#include <thread>

#include <base\time\time.h>
#include <base\timer\timer.h>
#include <base\message_loop\message_loop.h>

void TestFoo()
{
    base::debug::StackTrace trace;
    std::string callStack = trace.ToString();
    std::cout << "The call stack is:\n" << callStack;
}

void InvokeFoo( std::string parameter )
{
    std::cout << "Message passed in: " << parameter << std::endl;
    TestFoo();
}

class TestTimer
{

public:

    void StartDoingStuff()
    {
        timer_.Start( FROM_HERE, base::TimeDelta::FromSeconds( 2 ),
            this, &TestTimer::DoStuff );
    }

    void StopDoingStuff()
    {
        timer_.Stop();
    }

private:

    void DoStuff()
    {
        std::cout << "timer event handled\n";
    }
    base::RepeatingTimer timer_;
};

int main()
{
    InvokeFoo( "aa" );

    base::MessageLoop msgLoop;
    base::RunLoop loop;

    TestTimer my;
    my.StartDoingStuff();

    loop.Run();
}
