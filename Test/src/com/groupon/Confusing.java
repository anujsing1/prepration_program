package com.groupon;

public class Confusing {

	public Confusing(Object o){
		System.out.println("object");
	}
	
	public Confusing(double[] o){
		System.out.println("double");
	}
	
	/*public Confusing(Integer i){
		System.out.println("integer");
	}*/
	public static void main(String[] args) {
		new Confusing(null);
	}

}
