/**
 * 
 */
package com.study;


/**
 * @author govind.gupta
 *
 */
public class PersistentTest_Q7 {

	String name = "bleep";
	 void setName(String name){
		 this.name = name;
	 }
	 
	 void backgroundSetName() throws InterruptedException{
		 Thread t = new Thread(){
			 @Override
			 public void run(){
				 setName("Boom");
			 }
		 };
		 t.start();
		 t.join();
		 System.out.println(name);
	 }
	
	/**
	 * @param args
	 * @throws InterruptedException 
	 */
	public static void main(String[] args) throws InterruptedException {
		new PersistentTest_Q7().backgroundSetName();
	}
}
