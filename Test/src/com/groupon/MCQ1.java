package com.groupon;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public class MCQ1 {
	private String name;
	public MCQ1() {
		// TODO Auto-generated constructor stub
	}

	public MCQ1(String s) {
		this.name = s;
	}
	
	public int hashCode() {
		return name.hashCode();
	}
	
	public boolean equals(Object obj) {
		// TODO Auto-generated method stub
		return true;
	}

	public boolean equals(MCQ1 mcq1) {
		// TODO Auto-generated method stub
		return false;
	}
	
	public static void main(String[] args) {
		
		Map<String, String> test = new HashMap<>(); 
		
		MCQ1 mcq1 = new MCQ1("Hello");
		MCQ1 mcq2 = new MCQ1("Hello");
		
		System.out.println(mcq1.equals(mcq2));
		
		Map<MCQ1, String> testMap = new HashMap<MCQ1, String>();
		testMap.put(mcq1, "world");
		testMap.put(mcq2, "new");
		
		System.out.println(testMap.size());
		Set<MCQ1> testSet =  new HashSet<MCQ1>();
		testSet.add(mcq1);
		testSet.add(mcq2);
		System.out.println(testSet.size());
		
		
	}
}
