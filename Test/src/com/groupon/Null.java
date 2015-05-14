package com.groupon;

public class Null {

	static void greet(){
		System.out.println("Hello!");
	}
	
	public static void main(String[] args) {
		((Null) null).greet();
	}

}
