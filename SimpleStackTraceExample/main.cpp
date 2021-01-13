#include <iostream>
#include <base/debug/stack_trace.h>
#include "base\task\thread_pool\thread_pool.h"
#include <base\task\task_executor.h>
#include <base\task\thread_pool\thread_pool_impl.h>
#include <base\task\post_task.h>
#include "base/bind.h"
#include <base\callback.h>
#include <chrono>
#include <thread>

#include <VersionHelpers.h>

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
    base::ThreadPoolInstance::Create( "MyThreadPool" );
    base::ThreadPoolInstance::Get()->StartWithDefaultParams();

    base::PostTask( FROM_HERE,
        base::Bind( &InvokeFoo, "Yes then printed in thread pool." ) );

    std::cout << "Hello World!\n";
    std::this_thread::sleep_for( std::chrono::seconds( 30 ) );
}
