import asyncio
import time
import random
import httpx

BASE_URL = "https://baes-mock-exam.vercel.app/api"
NUM_STUDENTS = 200  # Start with 50, then bump to 100

async def simulate_student(client: httpx.AsyncClient, student_num: int):
    matric = f"TEST{student_num:03d}"
    start = time.perf_counter()
    
    try:
        # 1. Login
        login_res = await client.post(f"{BASE_URL}/login", json={"matric_no": matric})
        if login_res.status_code != 200:
            return matric, f"LOGIN FAIL ({login_res.status_code}): {login_res.text}", 0

        # 2. Fetch Questions
        q_res = await client.get(f"{BASE_URL}/questions", params={"matric_no": matric})
        if q_res.status_code != 200:
            return matric, f"QUESTIONS FAIL ({q_res.status_code})", 0
        
        questions = q_res.json().get("questions", [])
        
        # 3. Generate random answers
        answers = {q["id"]: random.randint(0, 3) for q in questions}

        # 4. Submit Exam
        sub_res = await client.post(
            f"{BASE_URL}/submit",
            json={"matric_no": matric, "answers": answers}
        )
        elapsed = round(time.perf_counter() - start, 2)
        
        if sub_res.status_code != 200:
            return matric, f"SUBMIT FAIL ({sub_res.status_code}): {sub_res.text}", elapsed
            
        return matric, "OK", elapsed

    except Exception as e:
        return matric, f"CRASH: {str(e)}", round(time.perf_counter() - start, 2)

async def main():
    print(f"🚀 Launching {NUM_STUDENTS} concurrent students against {BASE_URL}...")
    limits = httpx.Limits(max_connections=NUM_STUDENTS)
    async with httpx.AsyncClient(timeout=60.0, limits=limits) as client:
        tasks = [simulate_student(client, i) for i in range(1, NUM_STUDENTS + 1)]
        results = await asyncio.gather(*tasks)

    successes = [r for r in results if r[1] == "OK"]
    failures = [r for r in results if r[1] != "OK"]
    times = [r[2] for r in successes]

    print("\n--- STRESS TEST RESULTS ---")
    print(f"✅ Passed: {len(successes)} / {NUM_STUDENTS}")
    print(f"❌ Failed: {len(failures)} / {NUM_STUDENTS}")
    if times:
        print(f"⏱️  Avg Time: {round(sum(times)/len(times), 2)}s | Max Time: {max(times)}s")
    
    if failures:
        print("\nSample Failures:")
        for f in failures[:5]:
            print(" ", f)

if __name__ == "__main__":
    asyncio.run(main())