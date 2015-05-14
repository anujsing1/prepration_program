package com.groupon;

public class AnimalFarm {

	public static void main(String[] args) {
		final String pig = "length: 10";
		final String dog = "length: " + pig.length();
		System.out.print("Animals are equal:"+pig == dog);
	}

}
