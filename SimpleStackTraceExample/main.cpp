#include <iostream>
#include <base/debug/stack_trace.h>
#include "base/bind.h"
#include <base\callback.h>
#include <chrono>
#include <thread>

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

int main()
{
    InvokeFoo( "aa" );

    std::cout << "Hello World!\n";
    std::this_thread::sleep_for( std::chrono::seconds( 30 ) );
}
