package com.study;

import java.util.HashMap;
import java.util.Iterator;


public class HashMapHashCodeOverrideExmple {

	String name;
	long population;
	
	public HashMapHashCodeOverrideExmple(String name, long population) {
		super();
		this.name = name;
		this.population = population;
	}
	
	public String getName() {
		return name;
	}
	public void setName(String name) {
		this.name = name;
	}
	public long getPopulation() {
		return population;
	}
	public void setPopulation(long population) {
		this.population = population;
	}
	
	@Override
	public int hashCode() {
		if (this.name.length() % 2 == 0)
			return 31;
		else
			return 95;
	}	
	
	@Override
	public boolean equals(Object obj) {
		HashMapHashCodeOverrideExmple other = (HashMapHashCodeOverrideExmple) obj;
		if (name.equalsIgnoreCase((other.name)))
			return true;
		return false;
	}
	
	public static void main(String args[]){
		HashMapHashCodeOverrideExmple first = new HashMapHashCodeOverrideExmple("India", 1000);
		HashMapHashCodeOverrideExmple second = new HashMapHashCodeOverrideExmple("Japan", 10000);
		HashMapHashCodeOverrideExmple third = new HashMapHashCodeOverrideExmple("Franc", 2000);
		HashMapHashCodeOverrideExmple fourth = new HashMapHashCodeOverrideExmple("Russia", 20000);
		
		HashMap<HashMapHashCodeOverrideExmple, String> map = new HashMap<HashMapHashCodeOverrideExmple, String>();
		map.put(first, "Delhi");
		map.put(second, "Tokyo");
		map.put(third, "paris");
		map.put(fourth, "Moscow");
		
		Iterator<HashMapHashCodeOverrideExmple> iterator = map.keySet().iterator();
		while(iterator.hasNext()){
			HashMapHashCodeOverrideExmple obj = iterator.next();
			System.out.println(obj);
			System.out.println("Capital:"+map.get(obj) + "name:" +obj.name);
		}
	}
	

	
	
	}

